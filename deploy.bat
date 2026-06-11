scp -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no docker-compose.prod.yml nat0332624138@grapehrm.site:/home/nat0332624138/GrapeHRM/docker-compose.prod.yml
scp -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no backend\Dockerfile.prod nat0332624138@grapehrm.site:/home/nat0332624138/GrapeHRM/backend/Dockerfile.prod
scp -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no frontend\Dockerfile.prod nat0332624138@grapehrm.site:/home/nat0332624138/GrapeHRM/frontend/Dockerfile.prod
scp -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no frontend\nginx.conf nat0332624138@grapehrm.site:/home/nat0332624138/GrapeHRM/frontend/nginx.conf
scp -r -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no frontend\dist nat0332624138@grapehrm.site:/home/nat0332624138/GrapeHRM/frontend/
ssh -i C:\Users\ADMIN\.ssh\id_rsa -o StrictHostKeyChecking=no nat0332624138@grapehrm.site "cd /home/nat0332624138/GrapeHRM && sudo docker compose down && sudo docker compose up --build -d"
