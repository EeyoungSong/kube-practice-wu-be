# Jenkins 환경 변수 설정 가이드

## 1. Jenkins Credentials 설정

### 방법 1: Global Credentials (권장)

1. Jenkins 대시보드 → "Manage Jenkins" → "Manage Credentials"
2. "Global" domain 클릭
3. "Add Credentials" 선택

#### Secret Text로 각각 추가:

- **ID**: `DJANGO_SECRET_KEY`, **Secret**: `your-django-secret-key`
- **ID**: `DB_PASSWORD`, **Secret**: `your-database-password`
- **ID**: `OPENAI_API_KEY`, **Secret**: `your-openai-api-key`
- **ID**: `GOOGLE_CLIENT_ID`, **Secret**: `your-google-client-id`
- **ID**: `GOOGLE_CLIENT_SECRET`, **Secret**: `your-google-client-secret`

#### Username/Password로 추가:

- **ID**: `docker-hub-credentials`
- **Username**: Docker Hub 사용자명
- **Password**: Docker Hub 패스워드 (또는 토큰)

#### SSH Key 추가:

- **ID**: `ec2-ssh-key`
- **Kind**: SSH Username with private key
- **Username**: `ubuntu`
- **Private Key**: EC2 접속용 private key 내용

### 방법 2: Pipeline Job의 Environment Variables

Pipeline Job 설정에서:

1. "Build Environment" 섹션
2. "Environment variables" 체크
3. 다음 변수들 추가:

```
EC2_HOST=your-ec2-ip-address
ALLOWED_HOSTS=your-domain.com,your-ec2-ip
DB_NAME=django_app
DB_USER=postgres
```

## 2. 환경별 파일 관리 전략

### 개발 환경 (.env.local)

```bash
SECRET_KEY=dev-secret-key
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_NAME=django_dev
DB_USER=postgres
DB_PASSWORD=dev_password
```

### 스테이징 환경 (.env.staging)

```bash
SECRET_KEY=staging-secret-key
DEBUG=0
ALLOWED_HOSTS=staging.yourdomain.com
DB_HOST=staging-db
DB_NAME=django_staging
DB_USER=postgres
DB_PASSWORD=staging_password
```

### 프로덕션 환경 (.env.prod)

```bash
SECRET_KEY=prod-secret-key
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_HOST=prod-db
DB_NAME=django_prod
DB_USER=postgres
DB_PASSWORD=prod_password
```
