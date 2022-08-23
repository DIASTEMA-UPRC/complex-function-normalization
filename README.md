# Complex Function Normalization

## Description
DIASTEMA is implimenting a feature able to handle complex functions as rules made by the end-users. These functions are able to make processing jobs on different datasets to produce a new dataset containing valuable information [[1]](https://github.com/DIASTEMA-UPRC/complex-function-normalization/blob/main/README.md#references).

The ability to handle complex functions is done by first making a complex function (described as a JSON graph) as a simpler function. This is called the complex function normalization.

A simple description of the function normalization process is:
1. Get the complex graph (containing many different functions inside of it).
2. Parse the complex graph to find the functions used.
3. For every function in the complex graph, extract the operations inside of this function from the MongoDB library collection.
3.1. Then add the operations in the complex graph, to make it stop reffering to a function. This will make the complex graph to reffer only to simple operations.
3.2. In this step, a dynamic organization of the graph is happening to ensure the validity of the end operations,
3.3. Remove not needed nodes from the complex graph because of the new insertions.
4. In the end of the above process for all the existing functions, Remove the unneeded nodes from the complex graph because of the new insertions.

## Repository Contents
- function-normalization/docker-image
  - A repository with all the needed files to execute the Complex Function Normalization service using Docker.
- function-normalization/dummy-jsons
  - A repository containing files to test the above functionallity locally.

## Example of use
In this section, an example of how to use the source code of this repository is shown, using the files from the dummy-jsons repository.
### Prerequisites
Below is an example of prerequisites:
- Docker
- Windows OS
- MongoDB
- Postman

You can execute the functionality with other prerequisites and commands as well!

#### MongoDB Initialization
1. Open the MongoDB shell by typing "mongo" on a CMD and run the following commands:
```
use TEST
db.dropDatabase()
use TEST
db.library.insert( {"name":"Test_Add","output_type":"float","args":[{"type":"int","name":"val_1","arg_id":1},{"type":"float","name":"val_2","arg_id":2}],"expression":[{"id":"1","step":1,"from":0,"next":3,"info":{"kind":"arg","type":"int","name":"val_1","arg_id":1}},{"id":"2","step":2,"from":0,"next":3,"info":{"kind":"arg","type":"float","name":"val_2","arg_id":2}},{"id":"3","step":3,"from":[1,2],"next":0,"info":{"kind":"operation","name":"addition"}}]} )
db.library.insert( {"name":"Test_Func","output_type":"float","args":[{"type":"float","name":"val_1","arg_id":1},{"type":"float","name":"val_2","arg_id":2},{"type":"float","name":"val_3","arg_id":3}],"expression":[{"id":"4","step":1,"from":0,"next":3,"info":{"kind":"arg","type":"float","name":"val_1","arg_id":1}},{"id":"5","step":2,"from":0,"next":3,"info":{"kind":"arg","type":"float","name":"val_2","arg_id":2}},{"id":"6","step":3,"from":[1,2],"next":5,"info":{"kind":"operation","name":"subtraction"}},{"id":"7","step":4,"from":0,"next":5,"info":{"kind":"arg","type":"float","name":"val_3","arg_id":3}},{"id":"8","step":5,"from":[4,3],"next":0,"info":{"kind":"operation","name":"subtraction"}}]} )
db.library.insert( {"name":"Test_Logic","output_type":"boolean","args":[{"type":"boolean","name":"val_1","arg_id":1},{"type":"boolean","name":"val_2","arg_id":2}],"expression":[{"id":"1","step":1,"from":0,"next":3,"info":{"kind":"arg","type":"boolean","name":"val_1","arg_id":1}},{"id":"2","step":2,"from":0,"next":3,"info":{"kind":"arg","type":"boolean","name":"val_2","arg_id":2}},{"id":"3","step":3,"from":[1,2],"next":4,"info":{"kind":"operation","name":"logical_and"}},{"id":"4","step":4,"from":3,"next":0,"info":{"kind":"operation","name":"logical_not"}}]} )

```
The above can by copy and pasted from top to bottom and it will run automatically.
1.1. If it is needed, you can change the above commands to use another Database and Collection from the "TEST" database and "library" collection.
1.2. The two insertions are the JSONs named "Test_Add.json" and "Test_Func.json" from the "http://function-normalization/dummy-jsons" repository.
#### Service Startup
2. Open a CMD inside the "function-normalization/docker-image" folder.
3. Run the commands below:
```
docker build --tag function-normalization-server-image .
```
```
docker run -d -p 127.0.0.1:5000:5000 ^
--name function-normalization-server ^
--restart always ^
-e HOST=0.0.0.0 ^
-e PORT=5000 ^
-e MONGO_HOST=host.docker.internal ^
-e MONGO_PORT=27017 ^
-e DATABASE=TEST ^
-e COLLECTION=library ^
function-normalization-server-image
```
- Above, you can change the Mongo host and port if you have configured it.
- You can change the host and port of the service if needed as well.
- Also, you can configure the Database and Collections names if you are using another DB and Collection.

#### Usage
Now you have a library of simple functions and the service is running in your machine. Below you will input a complex graph in the Complex Function Normalization service and get its output.

4. Open Postman and execute the following request:
   - POST
   - URL: http://localhost:5000/normalize
   - JSON BODY: The "Test_Complex.json" from the repository named "function-normalization/dummy-jsons"

By executing the above request and getting a "STATUS CODE 200 OK" you will get responce with a simplified version of the Complex Function given into the service, ready to be inserted in the MongoDB library collection.

## References
- [1] https://diastema.gr/
