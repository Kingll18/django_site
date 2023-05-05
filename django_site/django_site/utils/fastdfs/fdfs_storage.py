from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储系统类"""

    def __init__(self, client_path=None, base_url=None):
        self.client_path = client_path or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        """
        用来打开文件的，但是我们自定义文件存储系统的目的是为了实现存储到远程FastDFS服务器，不需要打开文件，所以此方法没用
        :param name: 要打开的文件名
        :param mode: 打开文件的模式
        """
        pass

    def _save(self, name, content):
        """
        文件上传存储时会调用此方法，但此方法默认是向本地存储的吗。在此方法做实现文件存储到远程的FastDFS服务器
        :param name: 要上传的文件名
        :param content: 以rb模式打开的文件对象  将来通过content.read()  可以读取二进制数据
        """
        # 1. 创建conf文件对象
        conf = get_tracker_conf(self.client_path)

        # 2. 创建远程链接对象  FastDFS客户端
        client = Fdfs_client(conf)

        # 3. 通过客户端调用上传文件的方法，上传文件到DFS服务器
        # client.upload_by_filename() 只能通过文件的绝对路径上传 此方法上传的含义会有后缀(jpg,png,mp4)
        # upload_by_buffer 可以通过文件二进制数据进行上传  上传后没有后缀
        ret = client.upload_by_buffer(content.read())
        if ret.get('Status') != 'Upload successed.':
            raise Exception('Upload file failed !')

        # 4.获取file_id
        file_id = ret.get('Remote file_id').decode()

        # 5.返回
        return file_id

    def exists(self, name):
        """
        当我进行上传事调用此方法  判断是否已经上传  如果没有上传才会调用save方法进行上传
        :param name:  要上传的文件名
        :return: Bool  True （文件已存在，不需要上传）  False （则相反）
        """
        return False

    def url(self, name):
        """
        当要访问图片时  会调用此方法获取图片文件的绝对路径
        :param name: file_id
        :return: IP:8888 + file_id
        """
        return self.base_url + name
