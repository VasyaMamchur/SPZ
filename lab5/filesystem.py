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

    @staticmethod
    def register_descriptor(descriptor):
        ActiveFileSystem.FS.descriptors.append(descriptor)
        ActiveFileSystem.FS.descriptors_num += 1

    @staticmethod
    def check_path_exist(pathname: str, isLastFile: bool = False):
        if pathname == "":
            return ActiveFileSystem.CWD
        if pathname == '/':
            return ActiveFileSystem.FS.root
        pathArray = pathname.split('/')
        if pathname.startswith('/'):
            localCWD = ActiveFileSystem.FS.root
            pathArray.pop(0)
        else:
            localCWD = ActiveFileSystem.CWD
        new_localCWD = localCWD
        symlink_counter = 0
        if isLastFile:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    addons.print_error('Too much symlink')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = ActiveFileSystem.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j + ind + 1, symm)
                            break
                        elif j == len(pathArray) - 1 and localCWD.child_directories[i].descriptor.TYPE == 'regular':
                            return new_localCWD, localCWD.child_directories[i].descriptor
                        elif j == len(pathArray) - 1:
                            return None, None
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None, None
                localCWD = new_localCWD
                j += 1
            return new_localCWD
        else:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    addons.print_error('Too much symlink')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = ActiveFileSystem.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j + ind + 1, symm)
                            break
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None
                localCWD = new_localCWD
                j += 1
            return new_localCWD


class ActiveFileSystem:
    BLOCK_SIZE = 64
    MAX_FILE_NAME_LENGTH = 15
    FS = None
    CWD = None


class FileSystem:
    def __init__(self, descriptors_max_num):
        rootDescriptor = Descriptor(0, 'directory', 0, '/')
        rootDescriptor.links_num -= 1
        rootDirectory = Dir('/', rootDescriptor, None)
        ActiveFileSystem.CWD = rootDirectory
        self.descriptors_max_num = descriptors_max_num
        self.descriptors_num = 0
        self.descriptors = []
        self.descriptorsBitmap = [0 for i in range(descriptors_max_num)]
        self.Blocks = {}
        self.opened_files_num_descriptors = []
        self.opened_files = []
        self.descriptors.append(rootDescriptor)
        self.descriptors_num += 1
        self.descriptorsBitmap[0] = 1
        self.root = rootDirectory


class Descriptor:
    def __init__(self, num, file_type, length, name, content=None):
        self.NUM = num
        self.TYPE = file_type
        self.links_num = 1
        self.length = length
        self.blocks = []
        self.name = name
        self.links = [self]
        if file_type == 'symlink':
            self.content = content

    def show_info(self):
        print('%4d  %10s  %5d  %10d  %6d  %s' %
              (self.NUM,
               self.TYPE,
               self.links_num,
               self.length,
               len(self.blocks),
               f'{self.name}->{self.content}' if self.TYPE == 'symlink' else self.name))

    def show_statistics(self):
        print(f'#{self.NUM},{self.TYPE},link_num={self.links_num},length={self.length},blocks_num={len(self.blocks)},'
              f' name={self.name}' + f',symlink to {self.content}' if self.TYPE == 'symlink' else '')


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


class Symlink:
    def __init__(self, name: str, descriptor: Descriptor, parent, content):
        self.name = name
        self.descriptor = descriptor
        self.parent = parent
        self.content = content


class Dir:
    def __init__(self, name: str, descriptor: Descriptor, parent):
        self.name = name
        if parent is None:
            self.parent = self
        else:
            self.parent = parent
        self.descriptor = descriptor
        self.child_descriptors = []
        self.child_directories = []
        if parent is None:
            parentLink = Link(descriptor, '..')
        else:
            parentLink = Link(parent.descriptor, '..')
        self.child_descriptors.append(parentLink)
        self.child_descriptors.append(Link(descriptor, '.'))