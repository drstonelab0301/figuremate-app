# 🧠 FigureMate AI

**Context-Aware Knowledge Synthesis Engine**

FigureMate AI는 B2B 연구자, 엔지니어, 애널리스트를 위한 지능형 문서 분석 및 기술 보고서 생성 AI SaaS 템플릿입니다. 여러 개의 PDF 논문이나 기술 문서를 업로드하면, AI가 문서의 핵심 내용과 시각 자료(Figure)를 완벽하게 연결하여 전문가 수준의 기술 보고서를 자동으로 작성합니다.

---

## ✨ 핵심 기능 (Key Features)

- 📄 **Multi-Doc Parsing**: 최대 5개의 PDF(영문/국문) 문서를 한 번에 입력받아 방대한 지식을 1개의 맥락으로 병합합니다.
- 🖼️ **Contextual Image Extraction**: 문서 내의 Figure, Table, 논문 캡션 등을 AI가 식별하고, 보고서 본문 중 가장 설명이 잘 어울리는 위치에 이미지 원본을 정확하게 자동 배치합니다.
- 📝 **Professional Report Generation**: GPT-4o를 활용하여 단순 요약이 아닌, 서론-본론-결론-레퍼런스가 명확하게 구조화된 '수석 애널리스트' 수준의 전문적인 아티클을 작성합니다.
- 🎨 **Hero Image Generation**: DALL-E 3를 이용해 보고서의 주제를 함축하는 세련된 썸네일(Hero) 이미지를 상단에 생성합니다.
- ✏️ **Interactive AI Editor**: 생성된 결과물이 마음에 들지 않으면 하단의 채팅창에 수정 지시("더 짧게 요약해줘", "다시 한글로 써줘" 등)를 내리기만 하면, 이전 문맥과 이미지를 모두 유지한 채 즉시 보고서를 재작성합니다.
- 📥 **One-Click Export**: 마크다운(.md) 포맷으로 버튼 한 번에 전체 문서를 다운로드(Raw Base64 이미지 포함) 할 수 있어 Notion, GitHub, Obsidian 등 어디든 바로 붙여넣기 할 수 있습니다.

---

## 💻 설치 및 로컬 실행 방법 (Local Run)

### 1. 사전 준비 (Prerequisites)
- Python 3.9 이상
- OpenAI API Key (`sk-...`)

### 2. 패키지 설치
이 저장소를 클론(Clone)하거나 다운로드한 후, 터미널에서 아래 명령어를 실행하여 필수 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
streamlit run app.py
```
실행이 완료되면 브라우저에서 `http://localhost:8501` 주소로 FigureMate AI에 접속할 수 있습니다.

---

## 🚀 Streamlit Cloud 무료 배포 가이드 (Deployment)

자신만의 URL로 인터넷에 퍼블릭하게 서비스하고 싶다면 아래 과정을 따르세요. (무료)

1. **GitHub 업로드**: 이 `app.py`, `requirements.txt`, `README.md` 파일을 본인의 GitHub Public 저장소에 업로드합니다.
2. **Streamlit 연동**: [share.streamlit.io](https://share.streamlit.io/) 에 GitHub 계정으로 로그인합니다.
3. **New App 생성**: `New app` 버튼을 누르고 방금 코드를 올린 저장소와 브랜치를 선택한 뒤 메인 파일로 `app.py`를 지정합니다.
4. **App URL 설정**: 원하는 서브 도메인(예: `my-figuremate.streamlit.app`)을 설정하고 `Deploy`를 클릭합니다. 
5. 잠시 후 배포가 완료되면, 해당 URL을 통해 모바일/PC 어디서든 나만의 AI 애널리스트 툴에 접속할 수 있습니다!

---

## 🛠️ 기술 스택 (Tech Stack)
- **Frontend/Backend**: Streamlit (Python)
- **PDF Parsing**: PyMuPDF (`fitz`)
- **AI Core**: OpenAI API (GPT-4o, DALL-E 3)
- **Styling**: Custom Vanilla CSS (Pretendard & Inter Fonts)

---

*Powered by FigureMate AI & Streamlit*
