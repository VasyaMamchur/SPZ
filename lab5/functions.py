from filesystem import addons
from filesystem import ActiveFileSystem
from filesystem import FileSystem
from filesystem import Descriptor
from filesystem import Link
from filesystem import fd
from filesystem import Symlink
from filesystem import Dir

def mkfs(n):
    if ActiveFileSystem.FS is not None:
        addons.print_error('The file system was already been initialised')
        return
    ActiveFileSystem.FS = FileSystem(n)
    addons.print_ok('File system is initialised')


def stat(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            addons.print_descriptor_header()
            descriptor.show_statistics()
            return
    addons.print_error(f'There is no file with this name: {name}')


def ls(pathname=''):
    if addons.check_state():
        return
    if pathname == '':
        addons.print_descriptor_header()
        for descriptor in ActiveFileSystem.CWD.child_descriptors:
            descriptor.show_info()
        return
    if pathname == '/':
        addons.print_descriptor_header()
        for descriptor in ActiveFileSystem.FS.root:
            descriptor.show_info()
        return
    workingDir = addons.check_path_exist(pathname)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    addons.print_descriptor_header()
    for descriptor in workingDir.child_descriptors:
        descriptor.show_info()


def create(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    if len(str(descName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == name:
            addons.print_error('File with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = Descriptor(descriptor_num, 'regular', 0, descName)
    addons.register_descriptor(descriptor)
    workingDir.child_descriptors.append(descriptor)
    addons.print_descriptor_header()
    descriptor.show_info()


def link(name1, name2):
    if addons.check_state():
        return
    filePath = "/".join(name1.split('/')[:-1])
    if len(name1.split('/')) == 2 and filePath == '':
        filePath = '/'
    descFileName = name1.split('/')[-1]
    workingFileDir = addons.check_path_exist(filePath)
    if workingFileDir is None:
        addons.print_error(f"There is no directory with this path: {filePath}")
        return
    linkPath = "/".join(name2.split('/')[:-1])
    if len(name2.split('/')) == 2 and linkPath == '':
        linkPath = '/'
    descLinkName = name2.split('/')[-1]
    workingLinkDir = addons.check_path_exist(linkPath)
    if workingLinkDir is None:
        addons.print_error(f"There is no directory with this path: {linkPath}")
        return
    if len(str(descLinkName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    for descriptor in workingLinkDir.child_descriptors:
        if descriptor.name == descLinkName:
            addons.print_error(f'An instance with this name was already created {name2}')
            return
    for descriptor in workingFileDir.child_descriptors:
        if descriptor.name == descFileName:
            if isinstance(descriptor, Descriptor) and descriptor.TYPE == 'symlink':
                addons.print_error('We can\'t do link to symlink file')
                return
            if isinstance(descriptor, Link):
                addons.print_error('You can\'t create link to link')
                return
            new_link = Link(descriptor, descLinkName)
            descriptor.links.append(new_link)
            workingLinkDir.child_descriptors.append(new_link)
            addons.print_descriptor_header()
            new_link.show_info()
            return
    addons.print_error(f'There is no file with name {name1}')


def unlink(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f'There is no link with given name. It is a file.')
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, Descriptor):
                if descriptor.TYPE == 'directory':
                    addons.print_error('You can\'t unlink directory')
                    return
                workingDir.child_descriptors.remove(descriptor)
                descriptor.links_num -= 1
                if descriptor.links_num == 0:
                    ActiveFileSystem.FS.descriptorsBitmap[descriptor.NUM] = 0
                    del descriptor
                addons.print_ok('Unlinked')
            else:
                descriptor.descriptor.links_num -= 1
                descriptor.descriptor.links.remove(descriptor)
                workingDir.child_descriptors.remove(descriptor)
                if descriptor.descriptor.links_num == 0:
                    ActiveFileSystem.FS.descriptorsBitmap[descriptor.descriptor.NUM] = 0
                    del descriptor.descriptor
                addons.print_ok('Unlinked')
            return
    addons.print_error(f'There is no link with name {name}')


def symlink(string, pathname):
    if addons.check_state():
        return
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newSymName = pathname.split('/')[-1]
    if len(str(newSymName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
        return
    if newSymName == '':
        addons.print_error('Name could\'t be empty')
        return
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for directory in workingDir.child_directories:
        if newSymName == directory.name:
            addons.print_error('Directory with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newSymlinkDescriptor = Descriptor(descriptor_num, 'symlink', 0, newSymName, string)
    addons.register_descriptor(newSymlinkDescriptor)
    newSymlink = Symlink(newSymName, newSymlinkDescriptor, workingDir, string)
    workingDir.child_directories.append(newSymlink)
    workingDir.child_descriptors.append(newSymlinkDescriptor)


def open(name):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, Descriptor) and descriptor.TYPE == 'symlink':
                addons.print_error('We can\'t open symlink as file')
                return
            openedFile = fd(descriptor)
            ActiveFileSystem.FS.opened_files.append(openedFile)
            addons.print_ok(f'File {name} is opened with id {openedFile.num_descriptor}')
            return
    addons.print_error(f'There is no file with name {name}')


def close(fd):
    if addons.check_state():
        return
    if fd in ActiveFileSystem.FS.opened_files_num_descriptors:
        ActiveFileSystem.FS.opened_files_num_descriptors.remove(fd)
        for openedFile in ActiveFileSystem.FS.opened_files:
            if openedFile.num_descriptor == fd:
                ActiveFileSystem.FS.opened_files.remove(openedFile)
                del openedFile
                addons.print_ok(f'File with id {fd} is closed')
                return
    addons.print_error(f'There is no file opened with ID = {fd}')


def seek(fd, offset):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            openedFile.offset = offset
            addons.print_ok('Offset was set')
            return


def write(fd, size, val):
    if addons.check_state():
        return
    if len(str(val)) != 1:
        addons.print_error('Val should be 1 byte size')
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            num = len(openedFile.descriptor.blocks)
            while openedFile.offset + size > num * ActiveFileSystem.BLOCK_SIZE:
                openedFile.descriptor.blocks.append(['\0' for i in range(ActiveFileSystem.BLOCK_SIZE)])
                num += 1
            num = 0
            for i in range(openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                if i >= openedFile.offset:
                    openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = val
            if openedFile.descriptor.length < openedFile.offset + size:
                openedFile.descriptor.length = openedFile.offset + size
            addons.print_ok('Data were written to file')
            return


def read(fd, size):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with ID = {fd}')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            if openedFile.descriptor.length < openedFile.offset + size:
                addons.print_error(
                    f'File length is {openedFile.descriptor.length}. We can\'t read from {openedFile.offset} to {openedFile.offset + size}')
                return
            num = openedFile.offset // ActiveFileSystem.BLOCK_SIZE
            answer = ""
            for i in range(openedFile.offset, openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                answer += str(openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE])
            print(answer)


def truncate(name, size):
    if addons.check_state():
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName and descriptor.TYPE == 'regular':
            if size < descriptor.length:
                num = len(descriptor.blocks)
                while num * ActiveFileSystem.BLOCK_SIZE > size + ActiveFileSystem.BLOCK_SIZE:
                    descriptor.blocks.pop(num - 1)
                    num -= 1
                descriptor.length = size
            if size > descriptor.length:
                num = len(descriptor.blocks) - 1
                for i in range(descriptor.length, size):
                    if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                        descriptor.blocks.append(['\0' for i in range(ActiveFileSystem.BLOCK_SIZE)])
                        num += 1
                    descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = 0
                descriptor.length = size
            addons.print_ok(f'File {name} was successfully truncated')
            return
    addons.print_error(f'There is no file with path {name}')


def mkdir(pathname: str):
    if addons.check_state():
        return
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors were used')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newDirName = pathname.split('/')[-1]
    if len(str(newDirName)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    workingDir = addons.check_path_exist(oldPath)
    if workingDir is None:
        addons.print_error(f"There is no directory with this path: {oldPath}")
        return
    for directory in workingDir.child_directories:
        if newDirName == directory.name:
            addons.print_error('Directory with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newDirDescriptor = Descriptor(descriptor_num, 'directory', 0, newDirName)
    addons.register_descriptor(newDirDescriptor)
    newDir = Dir(newDirName, newDirDescriptor, workingDir)
    workingDir.child_descriptors.append(newDirDescriptor)
    workingDir.child_directories.append(newDir)
    addons.print_ok('Directory is created')


def rmdir(pathname):
    if addons.check_state():
        return
    if pathname == '/':
        addons.print_error('You can\'t delete root directory')
        return
    if pathname == '' or pathname == '.':
        addons.print_error('You can\'t delete current directory')
        return
    if pathname == '..':
        addons.print_error('It\'s unlogical to try delete directory that upper then other. Really? ')
        return
    oldDir = addons.check_path_exist(pathname)
    if oldDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    if len(oldDir.child_descriptors) != 2:
        addons.print_error('You can\'t delete nonempty dir')
        return
    if ActiveFileSystem.CWD == oldDir:
        addons.print_error('You can\'t delete directory you are in now ')
    oldDir.parent.child_descriptors.remove(oldDir.descriptor)
    oldDir.parent.child_directories.remove(oldDir)
    oldDir.child_descriptors.clear()
    oldDir.child_directories.clear()
    oldDir.parent.descriptor.links_num -= 1
    ActiveFileSystem.FS.descriptors.remove(oldDir.descriptor)
    ActiveFileSystem.FS.descriptorsBitmap[oldDir.descriptor.NUM] = 0
    ActiveFileSystem.FS.descriptors_num -= 1
    del oldDir.descriptor
    del oldDir
    addons.print_ok('Directory is deleted')


def cd(pathname):
    if addons.check_state():
        return
    if pathname == '/':
        ActiveFileSystem.CWD = ActiveFileSystem.FS.root
        addons.print_ok('Directory is changed')
        return
    newDir = addons.check_path_exist(pathname)
    if newDir is None:
        addons.print_error(f"There is no directory with this path: {pathname}")
        return
    ActiveFileSystem.CWD = newDir
    addons.print_ok('Directory is changed')


while True:
    try:
        answer_array = input('>>> ').split(' ')
        command = answer_array[0]
        if command == 'mkfs':
            mkfs(int(answer_array[1]))
        elif command == 'stat':
            stat(answer_array[1])
        elif command == 'ls':
            ls()
        elif command == 'create':
            create(answer_array[1])
        elif command == 'link':
            link(answer_array[1], answer_array[2])
        elif command == 'symlink':
            symlink(answer_array[1], answer_array[2])
        elif command == 'unlink':
            unlink(answer_array[1])
        elif command == 'open':
            open(answer_array[1])
        elif command == 'close':
            close(int(answer_array[1]))
        elif command == 'seek':
            seek(int(answer_array[1]), int(answer_array[2]))
        elif command == 'write':
            write(int(answer_array[1]), int(answer_array[2]), answer_array[3])
        elif command == 'read':
            read(int(answer_array[1]), int(answer_array[2]))
        elif command == 'truncate':
            truncate(answer_array[1], int(answer_array[2]))
        elif command == 'mkdir':
            mkdir(answer_array[1])
        elif command == 'rmdir':
            rmdir(answer_array[1])
        elif command == 'cd':
            cd(answer_array[1])
        elif command == 'exit':
            exit(0)
        else:
            addons.print_error('Unknown command')

    except NameError as error:
        addons.print_error('Error in function name')
    except SyntaxError as error:
        addons.print_error('Syntax error')
    except TypeError as error:
        addons.print_error('Arguments error')
    except ValueError as error:
        addons.print_error('Value error')
