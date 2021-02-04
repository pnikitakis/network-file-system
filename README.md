# network-file-system
Client/server application for accessing remote files. University project for Distributed Systems (Spring 2018).

## Description
Client can access remote files on server for reading and writing. Client has a virtual cache with LRU eviction policy.  

Operations supported:
- Find/create file (with flags: O_CREAT O_EXCL, O_TRUNC, O_RDWR, O_RDONLY, O_WRONLY)
- Read *n* bytes from file
- Write *n* bytes from file
- Change pointer position inside file
- Set client virtual cache validity

![Operation instructions](https://github.com/pnikitakis/network-file-system/blob/main/images/instructions.png)

A visual representation of the system can be found [here](https://github.com/pnikitakis/distributed-runtime/blob/main/Visual%20representation.pdf).

## Prerequisites
Python 3.6+

## How to run
Start the server script `server.py`. Then run on client `nfs_proto.py` to start the application. With `demo.py` we can access the network filesystem from the terminal. 

The `configuraton.py` file defines whether we include cache in our solution and it's size.


## Authors
- [Panagiotis Nikitakis](https://www.linkedin.com/in/panagiotis-nikitakis/)
- [Kalliopi Rantou](https://www.linkedin.com/in/kalliopi-rantou-6564981b4/)

## Course website
[ECE348 Distributed Systems](https://www.e-ce.uth.gr/studies/undergraduate/courses/ece348/?lang=en)  
Assigment instructions can be found [here](https://github.com/pnikitakis/network-file-system/blob/main/assigment_instructions_GR.pdf) **in Greek**.
