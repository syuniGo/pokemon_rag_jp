install-local:
	pip install -r local-requirements.txt

install:
	pip install -r requirements.txt

build:
	docker build -t flask-pokemon-app ./flask-app

run:
	docker run -p 8080:8080 -e FLASK_APP=main.py flask-pokemon-app flask run --host=0.0.0.0 --port=8080

test:
	flask --app main.py --debug run --host=0.0.0.0 --port=8084 --no-reload

docker-compose-up:
	docker-compose up --build

docker-compose-down:
	docker-compose down

clean:
	docker system prune -f

.PHONY: install-local install build run run-local docker-compose-up docker-compose-down clean

injest:
	python injest.py