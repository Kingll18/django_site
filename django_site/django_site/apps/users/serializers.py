import re
from django_redis import get_redis_connection
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User, Address
from goods.models import SKU


class CreateUserSerializer(serializers.ModelSerializer):
    """注册序列化器"""
    '''
        read_only  只用于序列化输出时使用   此字段不会进行反序列化的校验  (就算是错误的数据  也当做没有)
            只用来进行序列化输出   不用来校验(反序列化)
        write_only  只用于反序列化输入时使用   当序列化时，此字段将不会输出
            需要校验   但是不需要序列化输出
    '''
    # 序列化话器的所有字段(前端所需要传的): [username password password2 mobile sms_code allow]
    # 需要校验的字段：[username password password2 mobile sms_code allow]
    # 模型中已存在的字段：[username password mobile]

    # 需要返回给前端的字段[id username mobile]
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)  # 前端会传 'true' 和 'false'
    token = serializers.CharField(label="token", read_only=True)

    class Meta:
        model = User  # 从User模型中映射序列化器字段
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']
        extra_kwargs = {  # 修改字段选项
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义校验出错后的错误信息提示
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }

        }

    def validate_mobile(self, value):
        """单独校验手机号"""
        if not re.match('1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """是否同意协议校验"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):
        """校验两个密码是否正确相同"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两个密码不一致')

        # 校验验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = attrs['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # ！！！向redis存储数据时都是已字符串进行存储的，取出来的时候都是bytes类型
        if real_sms_code is None or attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('验证码错误')
        return attrs

    def create(self, validated_data):
        """重写创建方法  数据库操作"""
        '''
        user = User(
            username=validated_data['username'],
            mobile=validated_data['password'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user
        '''
        # 移除数据库模型类中不存在的属性
        # 把不需要的存储的password2，sms_code，allow从字典中移除
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        password = validated_data.pop('password')  # pop：删除password字段，并且将值记录到password python变量中
        user = User(**validated_data)
        user.set_password(password)  # 把密码加密后在赋值给user的password属性
        user.save()

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """用户个人中心"""

    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class EmailSerializer(serializers.ModelSerializer):
    """更新邮箱序列化器"""

    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {  # 修改字段选项
            'email': {'required': True}
        }

    def send_verify_email(self, to_email, verify_url):
        """
        发激活邮件
        @param to_email: 收件人邮箱
        @param verify_url: 邮箱激活url
        @return:
        """
        subject = "荣芊商城邮箱验证"
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用荣芊商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
        # send_mail(subject:标题, message:普通邮件正文, 发件人, [收件人], html_message: 超文本的邮件内容)
        send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)

    def update(self, instance, validated_data):
        """重写  因为我们还有发邮箱的操作在这里"""
        # 数据库修改操作  新增邮箱
        instance.email = validated_data.get('email')
        instance.save()  # ORM里面的save()
        '''-------发送邮箱--------'''
        # 生成校验连接
        verify_url = instance.generate_email_verify_url()
        # 发
        self.send_verify_email(to_email=instance.email, verify_url=verify_url)

        return instance


"""
receiver      收货人
province_id    省id
city_id   市id
district_id    区id
place   地址
mobile   手机号
tel   固定电话
email   电子邮箱
title  地址名称
"""


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    district = serializers.CharField(read_only=True)
    province_id = serializers.IntegerField(label="省ID", required=True)
    city_id = serializers.IntegerField(label="市ID", required=True)
    district_id = serializers.IntegerField(label="区ID", required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')  # 排除

    def validate_mobile(self, value):
        """校验手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        # 因为原来的create没有的user字段
        # self.context['request'].user   =========   request.user
        validated_data['user'] = self.context['request'].user
        print(validated_data['user'])
        # 还是使用源码里的create方法
        instance = super().create(validated_data)

        return instance


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """

    class Meta:
        model = Address
        fields = ('title',)


class UserBrowserHistorySerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(label="商品sku_id", min_value=1, required=True)

    def validate_sku_id(self, value):
        """单独对sku_id进行校验"""
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id不存在')
        return value

    def create(self, validated_data):
        sku_id = validated_data.get('sku_id')
        # 获取当前的用户的模型对象
        user = self.context['request'].user
        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        # 创建redis管道
        pl = redis_conn.pipeline()
        # 先去重
        pl.lrem('history_%d' % user.id, 0, sku_id)
        # 添加到开头
        pl.lpush('history_%d' % user.id, sku_id)
        # 截取前5个元素
        pl.ltrim('history_%d' % user.id, 0, 4)
        # 执行管道
        pl.execute()
        return validated_data


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']
