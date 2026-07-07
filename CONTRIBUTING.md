# Contribution guidelines:

## General guidelines:

* Abstract stuff as much as you can, design code in such a way that minimum hardcoding is done inside the code.

* IPs and any device specific parameters should be passed as sysargs while running the code.

* Write all communication requests/responses in terms of RPC calls. We use gRPC for the same.


## To run the code

### Basic setup:

* Clone this repository (this had pointed at the original, un-forked
  `zorroblue/distributed-search-engine` reference this project was built
  from - fixed to point at this repo instead)

	`git clone <this-repo-url>`

* Create a virtual environment venv if not done already

	`cd search-engine` <br>
	`python3 -m venv venv` <br>

* Install MongoDB (any current 6.x/7.x/8.x server works - pymongo 4.17+
  requires MongoDB 4.2+; the original "3.2.12" instruction predates that)

* Install [robomongo](https://askubuntu.com/questions/739297/how-to-install-robomongo-on-ubuntu/781793?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa) if you want to visualize the data changes on a GUI client(optional)

* Set up the database on the master and backup server
	
	`mongoimport --jsonArray -d masterdb -c indices data/indices.json` on master <br>

	`mongoimport --jsonArray -d backupdb -c indices data/indices.json` on backup of master`


* Set up the environment 

	`. environment.sh`


* Set up the required libraries

	`pip install -r requirements.txt`


* List the accessible replica servers in `replicas_list.txt`. The necessary setup as described above needs to be done. 
 
 ### Running the code

 #### To build the protobufs

 	python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. protos/search.proto

 ### Running the servers

Running `master.py`, `masterbackup.py` and `replica.py` with appropriate command line arguments should work. For running the crawler, use `crawler.py`. For demo purposes, we append the URLs in the URL list of 5 search terms with the input seed word during the writes. 
