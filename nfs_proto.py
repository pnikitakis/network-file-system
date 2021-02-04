#Rantou Kalliopi 2004, Nikitakis Panagiotis 1717
import socket
import os
import math
import configuration
import time

serverIP = ' '
serverPort = 0

file_fds = {}		#dictionary gia kathe arxeio: apothikeysh twn fds
fd_dict = {}		#dictionary gia kathe fd: apothikeush tou serfer fd, file position kai twn flags
cache_dic = {}
fd_counter = 0
secs = 0
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  	#create UDP connection


#sunarthsh gia thn apothikeush ip kai port tou server
def mynfs_set_srv_addr(ipaddr, port):
	global serverIP
	global serverPort
	
	serverIP = str(ipaddr)
	serverPort = int(port)
	
	return 0

#sunarthsh gia thn apostolh paketwn ston server
def send_packet(packet):
	global serverIP
	global serverPort
	global s
	
	print("--SEND PACKET TO SERVER: ", packet)
	data = None
	s.settimeout(2)

	#stelnei 3 fores kai an teleiwsei to timeout shmainei oti den labame apoanthsh apo server
	for i in range (0,3):
		s.sendto(packet, (serverIP, serverPort))
		try:
			data, addr = s.recvfrom(configuration.recvBufferSize)
			print("--RECEIVER PACKET FROM SERVER:", data)
			break
		except socket.timeout:
			print("Timeout!!! Try again...")
	
	#an ta data einia kena return error
	if data is None:
		return -1			#error den hrthe pote apanthsh
	
	#diaforetika slpit gia na paroume ta antisoixa pedia
	flag, restPacket = data.split(b',',1)
	
	#an open epistrofh server fd
	if flag == b'O':
		restPacket = restPacket.decode("utf-8")
		server_fd = int(restPacket)
		if server_fd == -1:
			return -2			#error apo pleura tou server
		else:
			return server_fd
	#an read epistrofh data pouu diabasthkan
	elif flag == b'R':
		try:
			flag_error, packet = restPacket.split(b',',1)
			flag_error = flag_error.decode("utf-8")
			flag_error = int(flag_error)
		except:
			restPacket = restPacket.decode("utf-8")
			flag_error = int(restPacket)
			
		#elegxos twn flag error
		if flag_error == -1:		#error apo pleura tou server
			return -2
		elif flag_error == -2:
			#protokolo gia epanafora katastasis ston server. an = -3 kalese thn open 
			return -3
		else:
			return packet
	#an write epistrofh twn bytes written
	elif flag == b'W':
		try:
			flag_error, bytes_written = restPacket.split(b',',1)
			flag_error = flag_error.decode("utf-8")
			flag_error = int(flag_error)
		except:
			restPacket = restPacket.decode("utf-8")
			flag_error = int(restPacket)
			
		#elegxos flag error
		if flag_error == -2:
			#protokolo gia epanafora katastasis ston server. an = -3 kalese thn open 
			return -3
		else:
			bytes_written = bytes_written.decode("utf-8")
			bytes_written = int(bytes_written)
			return bytes_written
	#an seek epistrofh megethos ou arxeiou
	elif flag == b'S':
		fsize = int(restPacket.decode("utf-8"))
		if fsize == -2: 
			return -3		#protokolo gia epanafora katastasis ston server. an = -3 kalese thn open
		else:
			return fsize
	
	#typical return. Den 8a ftasei pote edw
	return 0 


#sunarthsh gia thn epanafora tou server se periptosh pou to return einai -3
#to paketo 'O,fname,O_RDWR, server fd' wste o server na ksanadhmiourghsei th bash tou
def recover_server_fd(fd, server_fd):
	global file_fds
	global fd_dict
	
	fd = int(fd)
	server_fd = int(server_fd)
	for key, value in file_fds.items():
		if fd in value:
			fname = key
	packet = 'O,' + fname + ',O_RDWR,' + str(server_fd)
	packet = packet.encode("utf-8")
	print('packet to send: ', packet)
	send_packet(packet)
			
	return 0



def mynfs_set_cache_validity(seconds):
	global secs
	
	secs = int(seconds)
	
	return 0
	

#sunarthsh gia thn prosthiki block sthn cache apo thn read
def read_cache(server_fd, data, file_pos):
	global cache_dic
	total_blocks = 0
	
	for x in cache_dic.keys():			#eyresh posa bloacks yparxoun sthn cache 
		total_blocks += len(cache_dic[x])
	
	#cache is full
	print('Before cache change', cache_dic)
	if total_blocks >= configuration.cacheSize:
		# LRU 
		minLRU = time.time() #max timh h torinh stigmh
		for sfd in cache_dic.keys():
			for line in cache_dic[sfd]:
				if line[2] < minLRU:
					minLRU = line[2]
					delSfd = sfd
					delLine = cache_dic[sfd].index(line)
					
		#delete
		del cache_dic[delSfd][delLine]
		print('After cache replacement', cache_dic)
	
	#edw tha valw osa block xwrane
	if total_blocks < configuration.cacheSize:			#an xwraei na mprei to kainourio block
		if server_fd in cache_dic:		#an uparxei hdh to key
			cur_pos = 0
			
			for x in cache_dic[server_fd]:		#eyresh theshs sorted
				cur_pos += 1
				if x[0][0] > file_pos:
					break
			
			#prosthiki block taxinomhmena
			cache_dic[server_fd].insert(cur_pos, [[file_pos, len(data)],[data], time.time()])
		else:		#an den uparxei to key dhmiourgiatou block
			cache_dic[server_fd]=[[[file_pos, len(data)],[data], time.time()]]
			
		if len(data) < configuration.blockSize:
			return 1				#telos arxeiou ret=1
		else:
			return 0
		
	return 0

#sunarthsh gia thn prosthiki block sthn cache apo thn write
def write_cache(server_fd, data, file_pos, data_len):
	global cache_dic
	
	server_fd = int(server_fd)
	file_pos = int(file_pos)
	data_len = int(data_len)
	
	exist = False
	total_blocks = 0
	
	for x in cache_dic.keys():			#eyresh posa bloacks yparxoun sthn cache 
		total_blocks += len(cache_dic[x])
	
	
		#cache is full
	print('Before cache change', cache_dic)
	if total_blocks >= configuration.cacheSize:
		# LRU 
		minLRU = time.time() #max timh h torinh stigmh
		for sfd in cache_dic.keys():
			for line in cache_dic[sfd]:
				if line[2] < minLRU:
					minLRU = line[2]
					delSfd = sfd
					delLine = cache_dic[sfd].index(line)
					
		#delete
		del cache_dic[delSfd][delLine]
		print('After cache replacement', cache_dic)
		
		
	
	#edw tha valw osa block xwrane
	if total_blocks < configuration.cacheSize:	
		if server_fd in cache_dic:#an uparxei hdh to key
			for x in cache_dic[server_fd]:		#eueresh tou file_pos
				if x[0][0] == file_pos:		#orverwrite
					x[1] = [data]
					x[0][1] = data_len
					x[2] = time.time()
					break
				
		else:		#an den uparxei to key dhmiourgiatou block
			cache_dic[server_fd]=[]

	return 0

#sunarthsh gia thn dhmiourgia ths cache
#Otan to flagCache einai true oi sunarthseis xrhsimoopoioun ayth thn sunarthsh gia na steiloun ta paketa otus
def cache(packet, myfd):
	global cache_dic #dictionary ths cachee morfh:cache_dic[server_fd]=[[[file_pos, blockSize],[data]]]
	
	fd = int(myfd)
	tmp_packet = packet
	flag, rest_packet = tmp_packet.split(b',',1)
	
	#an to paketo afora th read
	if flag == b'R':
		rest_packet = rest_packet.decode("utf-8")
				
		server_fd , rest_packet = rest_packet.split(',',1)
		file_size , file_pos = rest_packet.split(',',1)
		
		server_fd = int(server_fd)
		file_size = int(file_size)
		file_pos = int(file_pos)
		blocks = math.ceil( float(file_size) / float(configuration.blockSize) )
		
		num_of_blocks = 0
		buf =[]
		
		while  file_size > 0:		#oso den exoume diabasei osa blocks prepei
			if server_fd in cache_dic.keys():#periptosi pou o server_fd einai mesa sthn cache
				if file_size > 0:		#oso den exoume diabasei osa blocks prepei
					for x in cache_dic[server_fd]:	#anazhthsh tou file position sthn cache
						#an to file_pos uparxei mesa sthn cache
						if file_pos >= x[0][0] and file_pos <= (x[0][0] + x[0][1] - 1): #gia 1 cache blovk poy uparxei
							#elegxos tou megetjous block se sxesh me to size pou zhtame
							if file_size >= (x[0][1] - (file_pos - x[0][0])):
								buf.append(x[1][0][(file_pos - x[0][0]): ])			#bazw ola ta upoloipa data ths cache
								file_size -= len(x[1][0][(file_pos - x[0][0]): ])	#meionetai to upoloipo pou prepei na diabasoyme
								file_pos += len(x[1][0][(file_pos - x[0][0]): ])	#proxarei o pos osa bytes diabasame
							else:
								buf.append(x[1][0][(file_pos - x[0][0]): (file_pos - x[0][0] + file_size)])
								file_pos += len(x[1][0][(file_pos - x[0][0]): (file_pos - x[0][0] + file_size)])
								file_size = 0
							
							num_of_blocks += 1 #diabasame ena block 
							if file_size == 0:
								break
							
						#periptwsh pou den uparxei to file pos pou zhthsame-->prepei na steiloume paketo gia to paroume
						elif ( file_pos < x[0][0] ) or ( file_pos >= cache_dic[server_fd][-1][0][0] + cache_dic[server_fd][-1][0][1] ):
							
							#eyeresh ths prwths theshs tou block sthn opoia anhkei to file_pos
							how_many = int(file_pos / configuration.blockSize) 

							cnt = 0
							cur_file_pos = 0
							while cnt < how_many:		#eyresh ths arxhs tou block pou zhtame
								cur_file_pos += configuration.blockSize	#arxh tou block
								cnt += 1
							
							#apostolh paetou gia na aproume to sugkekrimeno block
							packet = 'R,' + str(server_fd) + ',' + str(configuration.blockSize) + ',' + str(cur_file_pos)#ola se morfh str 
							packet = packet.encode("utf-8")
							
							ret = send_packet(packet)
							
							#error reboot
							while ret == -3:
								recover_server_fd(fd, server_fd)
								packet = 'R,' + str(server_fd) + ',' + str(configuration.blockSize)	+ ',' + str(cur_file_pos)	#ola se morfh str 
								packet = packet.encode("utf-8")
								print('packet to send: ', packet)
								ret = send_packet(packet)
							
							#error apo ton server h apo thn sundesh
							if(ret == -1):
								return -1
							elif ret == -2:
								return -2
							else :
								data = ret
								#paraabh data kai prosthiki sthn cche
								ret = read_cache(server_fd, data, cur_file_pos)#stelnw sthn arxh file_pos tou block
								
								#an ret = 0 oxi to telos tou arxeiou
								if ret == 0:
									pass
								elif ret == 1:	#telos arxeiou
									#elegxos an to megethos ppou theloume einai > , < , = me ta data pou exei  h cache
									if len(data) <= file_size:
										buf.append(cache_dic[server_fd][-1][1][0])
										file_size = 0
										
									elif len(data) > file_size:
										buf.append(cache_dic[server_fd][-1][1][0][:file_size+1])
										file_size = 0
								break		#break gia na ksekinisei pali to loop apo thn arxh giati balame nea cache line
							
							
			#mia fora tha ginei ayto gi ana dhmioyrghthei to arxeio kai meta tha paei panw sto fd in cache_dic
			elif server_fd not in cache_dic.keys():
				#poses fores apo to 0 prepei na prosthesw gia na brw thn axh tou block
				how_many = int(file_pos / configuration.blockSize)
				
				cnt = 0
				cur_file_pos = 0
				while cnt < how_many:		#eyresh ths arxhs tou block pou zhtame
					cur_file_pos += configuration.blockSize			#arxh tou block
					cnt += 1
				
					#ola se morfh str 
				packet = 'R,' + str(server_fd) + ',' + str(configuration.blockSize)	+ ',' + str(cur_file_pos)
				packet = packet.encode("utf-8")
				
				ret = send_packet(packet)
					
				while ret == -3:
					recover_server_fd(fd, server_fd)
					packet = 'R,' + str(server_fd) + ',' + str(configuration.blockSize)	+ ',' + str(cur_file_pos)	#ola se morfh str 
					packet = packet.encode("utf-8")
					print('packet to send: ', packet)
					#num_of_pack = size / 1024 #mporei allagh		#2o kommati
					ret = send_packet(packet)
				
				if(ret == -1):
					return -1
				elif ret == -2:
					return -1
				else :
					data = ret
					
					ret = read_cache(server_fd, data, cur_file_pos)
					#sunexizei sto eksoteriko while kai 8a mpei sto prwto IF
		print('***CACHE :', cache_dic)
		
		cnt = 0
		data = b''
		while cnt  < len(buf):
			data += buf[cnt]
			cnt += 1
		
		return data
	
	if flag == b'W':
		ret = send_packet(packet)
		
		while ret == -3:
			recover_server_fd(fd, server_fd)
			packet = 'W,' + str(server_fd) + ',' + str(file_pos) + ','	#ola se morfh str 
			packet = packet.encode("utf-8")
			packet = packet + data
			ret = send_packet(packet)
		
	
		if(ret == -1):
			return -1
		elif ret == -2:
			return -2
		else :
			bytes_written = ret
			temp_len = bytes_written
		
		print("bytes_written", bytes_written)
		
		server_fd , rest_packet = rest_packet.split(b',',1)
		file_pos , data = rest_packet.split(b',',1)
		
		server_fd = server_fd.decode("utf-8")
		server_fd = int(server_fd)
		file_pos = file_pos.decode("utf-8")
		file_pos = int(file_pos)

		blocks = math.ceil( float(len(data)) / float(configuration.blockSize) )
		temp_data = data
		data_len = 0
		
		num_of_blocks = 0
		
		while temp_len > 0:
			if server_fd in cache_dic.keys():
				if len(cache_dic[server_fd]) == 0:
					how_many = int(file_pos / configuration.blockSize) 	
					
					cnt = 0
					cur_file_pos = 0
					while cnt < how_many:		#eyresh ths arxhs tou block pou zhtame
						cur_file_pos += configuration.blockSize				#arxh tou block
						cnt += 1
					
					cur_pos = 0
					
					for x in cache_dic[server_fd]:		#eyresh theshs sorted
						cur_pos += 1
						if x[0][0] > file_pos:
							break
					#prosthiki block taxinomhmena
					cache_dic[server_fd].insert(cur_pos, [[cur_file_pos, configuration.blockSize],[], 0])
					
				for x in cache_dic[server_fd]:	#anazhthsh tou file position sthn cache
					temp_block = b''
					data_len = 0

					if file_pos >= x[0][0] and file_pos <= (x[0][0] + x[0][1] - 1): #gia 1 cache blovk poy uparxei
						#an ta data kalyptoun olo to block
						how_many = int(file_pos / configuration.blockSize) 	
						
						cnt = 0
						cur_file_pos = 0
						while cnt < how_many:		#eyresh ths arxhs tou block pou zhtame
							cur_file_pos += configuration.blockSize				#arxh tou block
							cnt += 1
						
						if (file_pos - cur_file_pos == 0): #ean einai sthn arxh toy block o pos
							if configuration.blockSize == temp_len:
								temp_block += temp_data
								data_len += len(temp_block)
								temp_len -= len(temp_data)
								
							elif configuration.blockSize > temp_len:
								temp_block += temp_data
								temp_len -= len(temp_data)
								data_len += len(temp_block)
								
								cnt = 0
								while cnt < configuration.blockSize - len(temp_data):
									temp_block += b'\00'
									cnt += 1
									
							elif configuration.blockSize < temp_len:
								print('3')
								temp_block += temp_data[:configuration.blockSize]
								data_len += len(temp_block)
								
								#allazw data wste na meinoun tosa osa prepei na fraftoun
								temp_data = temp_data[configuration.blockSize:]
								
								temp_len -= configuration.blockSize
							
								
						elif file_pos - cur_file_pos > 0:	#an uparxei keno sthn arxh
							cnt = 0
							while cnt < file_pos - cur_file_pos:
								temp_block += b'\00'
								cnt += 1
						
							#an mesa sto block exei meinei kenos xwros afou balame se sxesh me to megethos twn data
							#tote sumlhrwnw ta data kai stis upoloipes theseis null
							#sto len data xreiazomaste a meiwnetai akthe fora
							if configuration.blockSize -(file_pos - cur_file_pos) >= temp_len:
								temp_block += temp_data
								data_len += len(temp_block) - cnt
								temp_len -= len(temp_data)
								
								cnt_sec = 0
								while cnt_sec < configuration.blockSize -(file_pos - cur_file_pos + len(temp_data)):
									temp_block += b'\00'
									cnt_sec += 1
							else:
								#grafw tosa data mesa sto block osa xwrane
								temp_block += temp_data[:configuration.blockSize -(file_pos - cur_file_pos)+1]
								data_len += len(temp_block) - cnt
								
								#allazw data wste na meinoun tosa osa prepei na fraftoun
								temp_data = temp_data[configuration.blockSize -(file_pos - cur_file_pos)+1:]
								
								temp_len -= configuration.blockSize -(file_pos - cur_file_pos)

						write_cache(server_fd, temp_block, cur_file_pos, configuration.blockSize)
						
						num_of_blocks += 1 #diabasame ena block 
						file_pos += data_len
						print('file_pos', file_pos)
						print('temp_len:', temp_len)
					elif ( file_pos < x[0][0] ) or ( file_pos >= cache_dic[server_fd][-1][0][0] + cache_dic[server_fd][-1][0][1] ):
						how_many = int(file_pos / configuration.blockSize) 	
						
						cnt = 0
						cur_file_pos = 0
						while cnt < how_many:		#eyresh ths arxhs tou block pou zhtame
							cur_file_pos += configuration.blockSize				#arxh tou block
							cnt += 1
						
						cur_pos = 0
						
						for x in cache_dic[server_fd]:		#eyresh theshs sorted
							cur_pos += 1
							if x[0][0] > file_pos:
								break
						#prosthiki block taxinomhmena
						cache_dic[server_fd].insert(cur_pos, [[cur_file_pos, configuration.blockSize],[], 0])
					
						break
			elif server_fd not in cache_dic.keys():
				write_cache(server_fd, data, file_pos, data_len)
			
		print('***CACHE :', cache_dic)
		return bytes_written
			
def mynfs_open(fname, flags):
	global file_fds
	global fd_counter 
	global fd_dict
	
	flags_array = []
	
	fname = str(fname).strip()
	flags = str(flags)
	
	flags_array = flags.split('|') #pinakas me ola ta flags
	flags_array = [x.strip() for x in flags_array]
	
	#elegxos flags
	if 'O_CREAT' in flags_array and 'O_EXCL' in flags_array:
		if fname in file_fds:
			print("FLAG O_EXCL ERROR: File already exists!")
			return -1
	
	if 'O_RDWR' not in flags_array and 'O_WRONLY' not in flags_array and 'O_RDONLY' not in flags_array:
		print("FLAG ERROR: Need extra permissions!")
		return -1
	
	if fname not in file_fds or 'O_TRUNC' in flags_array:	
	#an to arxeio dne yparxei hdh sto dictionary ths efarmoghs h mas zhtaei truncate
		
		#apostolh se server
		packet = 'O,' + fname
		for x in flags_array:
			if x == 'O_CREAT' or x == 'O_EXCL' or x == 'O_TRUNC':
				packet = packet + ',' + x
		
		packet += ',-1' #teleutaio flag gia epanafora katastasis
		packet = packet.encode("utf-8")
		ret = send_packet(packet)
		
		if(ret == -1):
			print("ERROR: Server didn't answer!")
			return -1
		elif ret == -2:
			print("ERROR: Error from server side!")
			return -1
		else:
			server_fd = ret
	else:
		temp_fd = file_fds[fname][0] #pairnoume to 1o fd toy filename
		server_fd = fd_dict[temp_fd][0] #kai pairnoume to server fd gia to filename
		
	try:
		file_fds[fname].append(fd_counter) #yparxei hdh to filename
	except:
		file_fds[fname] = [fd_counter] #neo arxeio me to prwto toy fd
	
	
	if 'O_CREAT' in flags_array:
		flags_array.remove('O_CREAT')
	if 'O_EXCL' in flags_array:
		flags_array.remove('O_EXCL')
	if 'O_TRUNC' in flags_array:
		flags_array.remove('O_TRUNC')
			
	fd_dict[fd_counter] = [server_fd, 0, flags_array, 0]				#0 = SEEK_CUR
	
	ret = fd_counter
	fd_counter += 1
	
	return ret
	
	
def mynfs_read(fd, buf, size):
	global file_fds
	global fd_dict

	tmp_cnt = 0 #deutero kommati me cache
	fd = int(fd)
	size = str(size)

	server_fd = fd_dict[fd][0]		#antistoixos server fd
	file_pos = fd_dict[fd][1]
	flags = fd_dict[fd][2]		#elegxos sta flags an mporw na diabsw
	
	if 'O_RDONLY' not in flags and 'O_RDWR' not in flags:
		print("No permission for reading!")
		return -1 		# -4 gia flags error
	
	packet = 'R,' + str(server_fd) + ',' + size + ',' + str(file_pos)	#ola se morfh str 
	packet = packet.encode("utf-8")
	
	if configuration.flagCache == False:
		ret = send_packet(packet)
		
	else:
		ret = cache(packet, fd)
	
	while ret == -3:
		recover_server_fd(fd, server_fd)
		packet = 'R,' + str(server_fd) + ',' + size	+ ',' + str(file_pos)	#ola se morfh str 
		packet = packet.encode("utf-8")
		print('packet to send: ', packet)
		
		ret = send_packet(packet)

	if(ret == -1):
		print("ERROR: Server didn't answer!")
		return -1
	elif ret == -2:
		print("ERROR from server!")
		return -1
	else :
		data = ret
		data = data.replace(b'\00',b'')
		
		tmp_cnt += 1 #deutero kommati me cache
	
	fd_dict[fd][1] += len(data)
	buf = data								#buf += data		2o kommati
		
	return buf


def mynfs_write(fd, buf, size):
	global file_fds
	global fd_dict
	
	fd = int(fd)
	size = int(size)
	
	try:
		f = open(buf, 'rb')
		data = f.read(size)
		f.close()
	except:
		data = bytes(buf[:size],"utf-8")
		
			
	server_fd = fd_dict[fd][0]		#antistoixos server fd
	file_pos = fd_dict[fd][1]
	flags = fd_dict[fd][2]			#elegxos sta flags an mporw na diabsw
	
	if 'O_WRONLY' not in flags and 'O_RDWR' not in flags:
		print("No permission for reading!")
		return -1 		
	
	packet = 'W,' + str(server_fd) + ',' + str(file_pos) + ','	#ola se morfh str 
	packet = packet.encode("utf-8")
	packet = packet + data
	if configuration.flagCache == False:
		ret = send_packet(packet)
	else:
		ret = cache(packet, fd)
	
	
	while ret == -3:
		recover_server_fd(fd, server_fd)
		packet = 'W,' + str(server_fd) + ',' + str(file_pos) + ','	#ola se morfh str 
		packet = packet.encode("utf-8")
		packet = packet + data
		ret = send_packet(packet)
		
	
	if(ret == -1):
		print("ERROR: Server didn't answer!")
		return -1
	elif ret == -2:
		print("ERROR from server!")
		return -1
	else :
		bytes_written = ret
		fd_dict[fd][1] += bytes_written
		return bytes_written
	
	
def mynfs_seek(fd, pos, whence):
	global file_fds
	global fd_dict
	
	fd = int(fd)
	pos = int(pos)
	whence = int(whence)
	server_fd = fd_dict[fd][0]
	

	
	if whence == 0:
		fd_dict[fd][1] = pos #'os.SEEK_SET'
	elif whence == 1:
		fd_dict[fd][1] = fd_dict[fd][1] + pos #'os.SEEK_CUR'
	elif whence == 2:	#??? pws tha xerw pou einai to telos
		
		packet = ('S,' + str(server_fd)).encode('utf-8')
		ret = send_packet(packet)
		while ret == -3:
			#periptosi pou prepei na anoiksoume pali to arxeio
			#gia na broume to telos tou arxeiou
			recover_server_fd(fd, server_fd)
			packet = ('S,' + str(server_fd )).encode('utf-8')
			ret = send_packet(packet)
			
		fd_dict[fd][3] = ret #file size 
	
		fd_dict[fd][1] = fd_dict[fd][3] + pos #'os.SEEK_end'	
		
	return 0

def mynfs_close(fd):
	global file_fds
	global fd_dict
	
	fd = int(fd)
	
	del fd_dict[fd]
	
	for x in file_fds:
		if fd in file_fds[x]:
			file_fds[x].remove(fd)
			
	return 1