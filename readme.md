## Generate sample data in erp-core models
docker compose run django python manage.py migrate
docker compose run django python manage.py mock_data

## start the container
docker compose up -d --build

