# 🤖 Autobot: Network Automation Workflow Engine

Autobot은 복잡한 네트워크 관리 업무를 자동화하기 위해 설계된 워크플로우 엔진입니다. 특정 대역의 IP를 스캔하여 미사용 IP를 식별하고, 지정된 장비에 SSH로 접속하여 초기 설정을 자동으로 주입하는 통합 솔루션을 제공합니다.

---

## ✨ 주요 기능 (Key Features)

### 1. 🔍 지능형 IP 스캔 (IP Scan Module)
- **유연한 입력**: CIDR (e.g., `192.168.1.0/24`), 범위 (e.g., `192.168.1.1-100`), 개별 IP 리스트 지원.
- **듀얼 체크**: ICMP Ping을 통한 생존 확인 및 주요 포트(22, 80, 443) 소켓 스캔 병행.
- **상태 구분**: 'Active(사용 중)'와 'Available(미사용)' IP를 실시간으로 분류.

### 2. 📊 인벤토리 시각화 (Inventory & Visualization)
- **현황판**: 전체 스캔 수, 활성 IP, 사용 가능 IP에 대한 실시간 통계 제공.
- **미사용 IP 리스트**: 사용 가능한 IP만 별도로 모아 즉시 설정 작업으로 연결 가능.
- **데이터 내보내기**: 스캔 결과를 JSON 파일로 다운로드하여 이력 관리 가능.

### 3. 🚀 SSH 설정 자동 주입 (Configuration Push)
- **CLI 명령어 주입**: 멀티라인 에디터를 통해 여러 줄의 네트워크 명령어를 순차적으로 전송.
- **보안 강화**: 비밀번호 입력 시 마스킹 처리를 기본 적용.
- **지원 장비**: Cisco IOS, Arista, Juniper 등 Netmiko 지원 장비 호환 가능.

### 4. ✅ 결과 검증 및 로그 (Verification & Logging)
- **라이브 터미널**: 설정 주입 과정을 실시간 로그창에서 한눈에 확인.
- **명령어 검증**: 설정 완료 후 `show run` 등의 명령어를 실행하여 최종 상태 확인.
- **로그 저장**: 전체 작업 로그를 `.txt` 파일로 다운로드 가능.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11+
  - `FastAPI`: 고성능 비동기 API 서버
  - `Scapy`: 고급 네트워크 패킷 조작 (ARP/MAC 수집)
  - `Ping3`: ICMP 기반 네트워크 도달 상태 확인
  - `Netmiko`: 멀티 벤더 SSH 자동화 라이브러리
- **Frontend**: 
  - `Vanilla HTML5/CSS3`: 현대적인 Dark 테마 및 Glassmorphism 디자인
  - `Javascript`: 비동기 API 통신 및 동적 UI 업데이트

---

## ⚙️ 설치 및 실행 방법 (Installation & Usage)

### 1. 필수 라이브러리 설치
이 프로젝트는 네트워크 로우 레벨 접근 및 SSH 통신을 위해 다음 라이브러리들이 필요합니다.

```bash
pip install fastapi uvicorn netmiko ping3 scapy python-multipart
```

### 2. 애플리케이션 실행
서버를 실행하면 기본적으로 `8000` 포트에서 대시보드가 활성화됩니다.

```bash
python3 main.py
```

### 3. 대시보드 접속
브라우저를 열고 다음 주소로 이동합니다:
`http://localhost:8000`

---

## 📝 시스템 구조
```text
AutoBot/
├── main.py              # FastAPI 백엔드 엔진
├── static/              # 프론트엔드 자원
│   ├── index.html       # 메인 UI 구조
│   ├── style.css        # 스타일링 (Dark Theme)
│   └── script.js        # 비동기 제어 로직
└── README.md            # 프로젝트 가이드
```

---

## 🔒 보안 및 주의사항
- **관리자 권한**: ARP를 통한 MAC 주소 수집 기능은 OS 환경에 따라 `sudo` 권한이 필요할 수 있습니다.
- **네트워크 접근**: SSH 접속 대상 장비와 서버 간의 네트워크 경로(ACL, 방화벽)가 허용되어 있어야 합니다.
- **타임아웃**: 원격지 장비의 응답이 느릴 경우를 대비해 SSH 타임아웃 처리가 백엔드에 반영되어 있습니다.

---
**Autobot**은 네트워크 엔지니어의 반복적인 작업을 줄이고 실수 없는 설정을 돕기 위해 제작되었습니다. 🛠️
