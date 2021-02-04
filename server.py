#Rantou Kalliopi 2004, Nikitakis Panagiotis 1717, 
import socket
import queue
import threading
import os
import os.path
from random import randint

q = queue.Queue()

class serverThread(threading.Thread):		#sender thread
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		server_thread()


tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tmp.connect(("8.8.8.8", 80))
ipAddr = tmp.getsockname()[0]
tmp.close()

#take input for directory
directory = input('Give the directory of the file:\n')
directory = str(directory)

#dhmiourgia sundeshs
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((ipAddr, 0))
port = s.getsockname()[1]

print("----- Server -- IP: " + str(ipAddr) + " port: " + str(port)+" -----")

#thread pou epexergazetai to kathe neo mhnuma apo client
def server_thread():
	global q
	
	fd_cnt = randint(0,9999)
	
	file_fd_dict = {}		#dictionar gia kathe filename wste na apothikeuetai ton 
							#official fd kai ton fd pou stelnetais ton client
	
	while True:
		message, client_address = q.get()		#pairnoume mhnuma aop oura
		
		flag, rest_packet = message.split(b',',1)		#analoga me to flag tou mhnumatos epexergazomastw to mhnuma
		
		#morfh 'O,fd, flags'
		if flag == b'O':							#mhnyma gia open
			rest_packet = rest_packet.decode("utf-8")
			
			rest_packet , temp_fd = rest_packet.rsplit(',',1)

			temp_fd = int(temp_fd)
			
			try:		#elegxos gia an ew flags
				fname, rest_packet = rest_packet.split(',',1)
				fname = directory + fname
				flags_array = rest_packet.split(',')
				
				if  fname not in file_fd_dict:		#ean to arxeio den einai anoikto	
					#elegxos olwn twn periptwsewn gia ta flags
					if 'O_CREAT'in flags_array  and 'O_EXCL' in flags_array:
						if 'O_TRUNC' in flags_array:
							try:
								fd = os.open(fname, os.O_EXCL | os.O_CREAT | os.O_TRUNC | os.O_RDWR)
							except OSError:
								fd = -1					#shmatodotei error apo server
						else:
							try:
								fd = os.open(fname, os.O_EXCL | os.O_CREAT | os.O_RDWR)
							except OSError:
								fd = -1				#shmatodotei error apo server
					elif 'O_CREAT' in flags_array:
						if 'O_TRUNC' in flags_array:
							try:
								fd = os.open(fname, os.O_TRUNC | os.O_CREAT | os.O_RDWR)
							except OSError:
								fd = -1			#shmatodotei error apo server
						else:
							try:
								fd = os.open(fname, os.O_CREAT | os.O_RDWR)
							except OSError:
								fd = -1			#shmatodotei error apo server
					elif 'O_TRUNC' in flags_array:
						try:
							fd = os.open(fname, os.O_TRUNC | os.O_RDWR)
						except OSError:
							fd = -1
					
					if fd != -1:		#an den uparxei apotyxia ananewse ton  pinaka
						if temp_fd == -1:		#leitoirgei ws flag gia  reboot tou server
							file_fd_dict[fname]= [fd, fd_cnt]
							fd_cnt += 1
						else:
							file_fd_dict[fname]= [fd, temp_fd]	#to arxeio uparxei hdh sthn pleura tou server me fd =temp_fd
							
				else: #to arxeio einai anoixto alla hr8e flag O_TRUNC
					if 'O_TRUNC' in flags_array:
						if 'O_CREAT' in flags_array and 'O_EXCL' in flags_array: #error giati uparxei to arxeio
							s.sendto(b'O,-1', client_address)
							continue
						#truncate to arxeio
						os.truncate(file_fd_dict[fname][0], 0)
			except:			#flag einai O_RDONLY H O_WRONLY H O_RDWR
				fname = rest_packet
				fname = directory + fname
				if  fname not in file_fd_dict:
					try:
						fd = os.open(fname, os.O_RDWR)
					except OSError:
						fd = -1			#shmatodotei error apo server
				
					if fd != -1:#an den uparxei apotyxia ananewse ton  pinaka
						if temp_fd == -1:
							file_fd_dict[fname]= [fd, fd_cnt]
							fd_cnt += 1
						else:
							file_fd_dict[fname]= [fd, temp_fd]
			
			#dhmiourgia paketou epistrofhhs
			if fd != -1:
				ret_fd = file_fd_dict[fname][1]			#teika epistrefoume ton fd tou pinaka (-1 h ton swsto airthmo)
				packet = ('O,' + str(ret_fd)).encode("utf-8")
			else:
				packet = ('O,-1').encode("utf-8")		#diaforetika epistrefoume apotyxia
			
			s.sendto(packet, client_address)
		#morfh 'R,fd,size,pos'
		elif flag == b'R':
			rest_packet = rest_packet.decode("utf-8")
			
			server_fd , rest_packet = rest_packet.split(',',1)
			file_size , file_pos = rest_packet.split(',',1)
			
			server_fd = int(server_fd)
			file_size = int(file_size)
			file_pos = int(file_pos)

			for x in file_fd_dict:				#eyresh tou server fd pou antisoixei ston fd
				if server_fd != file_fd_dict[x][1]:
					ret = -2			#epistrofh latous, den uparxei o fd pou zhththike
				else:
					fd = file_fd_dict[x][0]		#diaforetika 
					ret = 0
					break
			
			#an uparxe o zhtoumenos fd
			if ret == 0:
				os.lseek(fd, file_pos, 0)#metainhsh tou fd kata poses theseis zhthsei o xrhsths

				data = os.read(fd, file_size)
				
				#epistofh paketou me ton antisoixo kwdiko
				packet = ('R,' + str(ret) + ',').encode("utf-8") + data
			elif ret == -2:
				packet = ('R,' + str(ret)).encode("utf-8")
				
			s.sendto(packet, client_address)			#send se for me to posa paketa antisoixoun sto input otu xrhsth
		#morfh 'W,fd,pos,data'
		elif flag == b'W':
			server_fd , rest_packet = rest_packet.split(b',',1)
			file_pos , data = rest_packet.split(b',',1)
			
			server_fd = server_fd.decode("utf-8")
			file_pos = file_pos.decode("utf-8")
			
			server_fd = int(server_fd)
			file_pos = int(file_pos)
			
			
			for x in file_fd_dict:				#eyresh tou server fd pou antisoixei ston fd
				if server_fd != file_fd_dict[x][1]:	
					ret = -2		#an o fd den brethike epistoffh lathous
				else:
					fd = file_fd_dict[x][0]
					ret = 0
					break
			
			#an uparxe o zhtoumenos fd
			if ret == 0:
				os.lseek(fd, file_pos, 0)#metainhsh tou fd kata poses theseis zhthsei o xrhsths
				
				bytes_written = os.write(fd, data)
				
				packet = ('W,' + str(ret) + ',' + str(bytes_written)).encode("utf-8")
			elif ret == -2:
				packet = ('W,' + str(ret)).encode("utf-8")

			#dhmiourgia paketou me antisoixo kwdiko lathous
			s.sendto(packet, client_address)		
		#morfh 'S,fd'	
		elif flag == b'S':
			rest_packet = rest_packet.decode("utf-8")
			
			fd = int(rest_packet)
			
			for x in file_fd_dict:				#eyresh tou server fd pou antisoixei ston fd
				if fd != file_fd_dict[x][1]:
					ret = -2
				else:
					file_name = x
					file_size = os.stat(file_name).st_size		#eyeresh tou size oloklhrou tou arxeiou
					ret = file_size
					break
			
			#epistrofh paketou me to megethos tou arxeiou
			packet = ('S,' + str(ret)).encode("utf-8")
			s.sendto(packet, client_address)	
	
		print("----- file_fd_dict: ", file_fd_dict)
			
th = serverThread()
th.start()

while True:
	message, address = s.recvfrom(32384)		#!!!prosarmogh megethous bytes
	
	q.put([message,address])		#dhmiourgia ouras gia thn apothikeush mhnymatwn


