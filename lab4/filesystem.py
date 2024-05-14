class addons:
    @staticmethod
    def print_error(*message):
        print('\033[91m', *message, '\033[0m')

    @staticmethod
    def print_ok(*message):
        print('\033[92m', *message, '\033[0m')

    @staticmethod
    def print_descriptor_header():
        print('   №        type  links      length  blocks  name')

    @staticmethod
    def check_state():
        if ActiveFileSystem.FS is None:
            addons.print_error('The file system is not initialised')
            return 1
        return 0


class ActiveFileSystem:
    BLOCK_SIZE = 64
    MAX_FILE_NAME_LENGTH = 15
    FS = None


class FileSystem:
    def __init__(self, des_n):
        self.descriptors_max_num = des_n
        self.descriptors_num = 0
        self.descriptors = []
        self.descriptorsBitmap = [0 for _ in range(des_n)]
        self.Blocks = {}
        self.opened_files_num_descriptors = []
        self.opened_files = []


class Descriptor:
    def __init__(self, num, file_type, length, name):
        self.NUM = num
        self.TYPE = file_type
        self.links_num = 1
        self.length = length
        self.blocks = []
        self.name = name
        self.links = [self]

    def show_info(self):
        print(
            '%4d  %10s  %5d  %10d  %6d  %s' %
            (self.NUM,
             self.TYPE,
             self.links_num,
             self.length,
             len(self.blocks),
             self.name))

    def show_statistics(self):
        print(f'#{self.NUM}, {self.TYPE}, links_num={self.links_num}, length={self.length},'
              f' blocks_num={len(self.blocks)}, name={self.name}')


class Link:
    def __init__(self, descriptor, name):
        descriptor.links_num += 1
        self.descriptor = descriptor
        self.name = name

    def show_info(self):
        print('%4d  %10s  %5d  %10d  %6d  %s' %
              (self.descriptor.NUM,
               self.descriptor.TYPE,
               self.descriptor.links_num,
               self.descriptor.length,
               len(self.descriptor.blocks),
               f'{self.name}->{self.descriptor.name}'))

    def show_statistics(self):
        print(f'#{self.descriptor.NUM}, {self.descriptor.TYPE}, links_num={self.descriptor.links_num},'
              f' length={self.descriptor.length}, blocks_num={len(self.descriptor.blocks)},'
              f' name={self.name} links to {self.descriptor.name}')


class fd:
    def __init__(self, descriptor):
        if isinstance(descriptor, Link):
            self.descriptor = descriptor.descriptor
        else:
            self.descriptor = descriptor
        num_desc = 0
        while num_desc in ActiveFileSystem.FS.opened_files_num_descriptors:
            num_desc += 1
        ActiveFileSystem.FS.opened_files_num_descriptors.append(num_desc)
        self.num_descriptor = num_desc
        self.offset = 0


