pipeline {
    agent any

    environment {
        // Docker 이미지 정보
        DOCKER_IMAGE = "django-ocr-app"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_REGISTRY = "your-docker-registry" // 필요시 Docker Hub 또는 ECR 주소
        
        // AWS 정보
        AWS_REGION = "ap-northeast-2"
        EC2_HOST = "${env.EC2_HOST}"
        EC2_USER = "ubuntu"
        
        // 환경 변수
        COMPOSE_FILE = "docker-compose.prod.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Environment Setup') {
            steps {
                script {
                    // Jenkins Credentials에서 환경 변수 가져와서 .env 파일 생성
                    withCredentials([
                        string(credentialsId: 'DJANGO_SECRET_KEY', variable: 'SECRET_KEY'),
                        string(credentialsId: 'DB_PASSWORD', variable: 'DB_PASSWORD'),
                        string(credentialsId: 'OPENAI_API_KEY', variable: 'OPENAI_API_KEY'),
                        string(credentialsId: 'GOOGLE_CLIENT_ID', variable: 'GOOGLE_CLIENT_ID'),
                        string(credentialsId: 'GOOGLE_CLIENT_SECRET', variable: 'GOOGLE_CLIENT_SECRET')
                    ]) {
                        sh '''
                            echo "Creating .env file from Jenkins credentials..."
                            cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=0
ALLOWED_HOSTS=${ALLOWED_HOSTS}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=db
DB_PORT=5432
OPENAI_API_KEY=${OPENAI_API_KEY}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
EOF
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def image = docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.withRegistry('', 'docker-hub-credentials') {
                        image.push()
                        image.push("latest")
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    // Docker Compose로 테스트 환경 구성
                    sh '''
                        docker-compose -f docker-compose.test.yml up --build -d
                        docker-compose -f docker-compose.test.yml exec -T web python manage.py test
                        docker-compose -f docker-compose.test.yml down
                    '''
                }
            }
        }

        stage('Deploy to EC2') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // SSH를 통해 EC2에 배포
                    sshagent(['ec2-ssh-key']) {
                        sh '''
                            # EC2 서버에 파일 복사
                            scp -o StrictHostKeyChecking=no docker-compose.prod.yml ${EC2_USER}@${EC2_HOST}:~/
                            scp -o StrictHostKeyChecking=no .env ${EC2_USER}@${EC2_HOST}:~/
                            
                            # EC2 서버에서 배포 실행
                            ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
                                # Docker 및 Docker Compose 설치 확인
                                if ! command -v docker &> /dev/null; then
                                    sudo apt-get update
                                    sudo apt-get install -y docker.io docker-compose
                                    sudo usermod -aG docker $USER
                                fi
                                
                                # 기존 컨테이너 중지 및 제거
                                docker-compose -f docker-compose.prod.yml down || true
                                
                                # 새로운 이미지 pull 및 실행
                                docker-compose -f docker-compose.prod.yml pull
                                docker-compose -f docker-compose.prod.yml up -d
                                
                                # 헬스 체크
                                sleep 30
                                curl -f http://localhost:8000/health/ || exit 1
ENDSSH
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            // 정리 작업
            sh '''
                docker system prune -f || true
            '''
        }
        success {
            echo '배포가 성공적으로 완료되었습니다!'
        }
        failure {
            echo '배포 중 오류가 발생했습니다.'
        }
    }
} 