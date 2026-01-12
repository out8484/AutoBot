# 🤖 Autobot: Network Automation Workflow Engine

Autobot은 복잡한 네트워크 관리 업무를 자동화하기 위해 설계된 강력한 워크플로우 엔진입니다. 'Modern Blue' 스타일의 프리미엄 UI를 통해 네트워크 스캔, 자산 관리, 설정 주입 및 실시간 검증을 통합적으로 관리할 수 있습니다.

---

## ✨ 주요 기능 (Key Features)

### 1. 🔍 지능형 IP 스캔 (IP Scan Module)
- **유연한 대역 지원**: CIDR (e.g., `172.27.14.0/24`), IP 범위, 개별 IP 리스트를 지원합니다.
- **다중 스캔 기법**:
  - **Remote Nmap**: 점프 호스트를 통한 원격 nmap 스캔으로 대규모 대역의 활성 호스트를 빠르게 식별합니다. (Jump Host 지원)
  - **ICMP Ping**: 네트워크 도달 가능성을 확인합니다.
  - **Port Scan**: SSH(22), HTTP(80), HTTPS(443) 포트 개방 여부를 체크합니다.
- **실시간 데이터 동기화**: 스캔 결과에서 IP를 체크박스로 선택하여 'Config Push' 메뉴로 즉시 전송할 수 있습니다.
- **Quick Actions (수동 진단)**: 스캔된 IP를 클릭하여 즉시 Ping 테스트를 수행하거나 시스템 기본 SSH/Telnet 클라이언트를 호출할 수 있습니다.

### 2. 🚀 스마트 설정 주입 (Step-by-Step Config Push)
- **동적 변수 감지 (Any {{key}} Detection)**: 설정 템플릿 내에 `{{변수}}` 형식을 입력하면 실시간으로 전용 입력 칸이 생성됩니다.
- **2단계 확정 프로세스 (Preview & Commit)**:
  1. **Preview**: 변수가 치환된 최종 설정 내용을 팝업으로 미리 확인하여 실수를 방지합니다.
  2. **Commit**: 최종 확인 후 버튼을 눌러야만 장비에 설정이 반영되는 안전한 메커니즘을 제공합니다.
- **실시간 NETCONF 로그**: Juniper PyEZ를 활용하여 세션 연결, DB Lock, 설정 로드, Commit 전 과정을 터미널 스타일로 실시간 중계합니다.

### 3. 🎨 프리미엄 UI/UX (Modern Blue Aesthetics)
- **Modern Blue 테마**: 깊이감 있는 네이비 블루와 사이언 포인트 컬러가 조화된 고품격 인터페이스.
- **글래스모피즘(Glassmorphism)**: 반투명 카드와 아름다운 그라데이션 광원을 활용한 현대적인 디자인.
- **반응형 대시보드**: 전체 스캔 통계 및 가용 IP 현황을 한눈에 파악할 수 있는 대시보드를 제공합니다.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11+
  - `FastAPI`: 고성능 비동기 API 서버
  - `junos-eznc (PyEZ)`: Juniper 전용 NETCONF 자동화
  - `Scapy`: 고급 네트워크 패킷 분석 (ARP/MAC 수집)
  - `Netmiko`: 멀티 벤더 SSH 자동화 및 점프 호스트 연동
  - `Ping3`: ICMP 네트워크 진단
- **Frontend**: 
  - `Vanilla HTML5/CSS3`: 커스텀 Modern Blue 테마 및 애니메이션
  - `Javascript (ES6+)`: 비동기 API 통신 및 실시간 프록시 UI 로직

---

## ⚙️ 설치 및 실행 방법 (Installation & Usage)

### 1. 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 애플리케이션 실행
```bash
python3 main.py
```
서버는 기본적으로 `http://0.0.0.0:8000`에서 활성화됩니다. 클라우드 배포(Streamlit, Heroku 등) 시에는 `PORT` 환경 변수를 자동으로 감지하여 바인딩합니다.

---

## 📝 시스템 구조
```text
AutoBot/
├── main.py              # FastAPI 백엔드 (API & Business Logic)
├── credentials.json     # 저장된 사용자 그룹 정보 (자동 생성)
├── static/              # 프론트엔드 리소스
│   ├── index.html       # 메인 UI 구조
│   ├── style.css        # Modern Blue 테마 스타일링
│   └── script.js        # 대화형 UI 제어 및 API 통신
└── README.md            # 상세 가이드
```

---

## 🔒 보안 및 운영 안내
- **권한 관리**: ARP Scan 기능을 위해 실행 환경에 따라 관리자 권한(`sudo`)이 필요할 수 있습니다.
- **데이터 보호**: 장비 접속 정보(비밀번호 등)는 로컬 `credentials.json`에 저장되므로 외부 유출에 주의하십시오.
- **장비 호환성**: 본 엔진은 Juniper Junos 장비를 기본 타겟으로 최적화되어 있으나, Netmiko를 통해 타 벤더 장비 확장도 가능합니다.

---
**Autobot**은 네트워크 엔지니어의 안정적이고 시각적인 자동화 여정을 지원합니다. 🛠️🌐
