echo '------------ base test ------------'
ab -c 50 -n 1000 http://localhost:8000/base-test


echo '------------ rest + resolver ------------'
ab -c 50 -n 1000 http://localhost:8000/sprints


echo '------------ graphql'------------ 
ab -c 50 -n 1000 -T "application/json" -p body.json http://localhost:8000/graphql
