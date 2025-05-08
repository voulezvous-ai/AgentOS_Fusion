run:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

logs:
	docker compose logs -f

up:
	docker compose up -d --build

down:
	docker compose down

deploy:
	git add . && git commit -m "deploy" && git push origin main
