import nfs_proto as nfs
import os
import os.path

ip = input('Give server IP: ')
port = input('Give server port: ')

nfs.mynfs_set_srv_addr(ip, int(port))

while True:
	command = input('\n---\nGive command\no : open \nr : read\nw : write\ns : seek\nc : close\n')
	if command == 'o':
		fname = input('Give file name: ')
		flags = input('Give flags: ')
		fd = nfs.mynfs_open(fname, flags)
		if fd == -1:
			print('\nContinuing with the next command\n\n')
			continue
		else:
			print('\nFile ['+ fname +'] opened, with fd = ' + str(fd))
	elif command == 'r':
		tmp_fd = input('Give fd: ')
		bytesToRead = input('Give number of bytes to read: ')
		bytesToRead = int(bytesToRead)
		data = nfs.mynfs_read(tmp_fd ,'', bytesToRead)
		if data == -1:
			print('\nContinuing with the next command\n\n')
			continue
		print('\nData recieved: ', data)
			
	elif command == 'w':
		tmp_fd = input('Give fd: ')
		tmp_fd = int(tmp_fd)
		inp = input('Give input: ')
		numBytes = input('Give number of bytes to write: ')
		numBytes = int(numBytes)
		isFile = os.path.isfile(inp) 
		if isFile == True:
			f = open(inp, 'rb')
			bytesToWrite = f.read(numBytes)
		else:
			bytesToWrite = inp[:numBytes]
		numofb = nfs.mynfs_write(tmp_fd, bytesToWrite, len(bytesToWrite))
		if numofb == -1:
			print('\nContinuing with the next command\n\n')
			continue
		else:
			print('Bytes written in file: ', numofb)
	elif command == 's':
		tmp_fd = input('Give fd: ')
		whence = input('Give whence:\n0 : SEEK_START\n1 : SEEK_CURR\n2 : SEEK_END\n')
		whence = int(whence)
		bytesoffset = input('Give bytes offset: ')
		bytesoffset = int(bytesoffset)
		nfs.mynfs_seek(tmp_fd, bytesoffset, whence)
		
	elif command == 'c':
		tmp_fd = input('Give fd: ')
		tmp_fd = int(tmp_fd)
		nfs.mynfs_close(tmp_fd)

	
