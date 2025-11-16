import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptLoader:
    """언어별 프롬프트 파일을 로드하고 템플릿 처리하는 클래스"""
    
    def __init__(self):
        # 현재 파일의 부모 디렉토리에서 prompts 폴더 경로 찾기
        current_dir = Path(__file__).parent.parent
        self.prompts_dir = current_dir / "prompts"
        
        # 지원하는 언어와 파일명 매핑
        self.language_files = {
            'english': 'english_prompt.txt',
            'chinese': 'chinese_prompt.txt', 
            'spanish': 'spanish_prompt.txt'
        }
    
    def load_prompt(self, language: str, sentence: str) -> str:
        """
        지정된 언어의 프롬프트를 로드하고 문장을 삽입하여 반환
        
        Args:
            language (str): 언어 코드 ('english', 'chinese', 'spanish')
            sentence (str): 분석할 문장
            
        Returns:
            str: 완성된 프롬프트 문자열
            
        Raises:
            FileNotFoundError: 프롬프트 파일이 없는 경우
            ValueError: 지원하지 않는 언어인 경우
        """
        if language not in self.language_files:
            raise ValueError(f"지원하지 않는 언어입니다: {language}. 지원 언어: {list(self.language_files.keys())}")
        
        prompt_file = self.prompts_dir / self.language_files[language]
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {prompt_file}")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 문장 삽입 (템플릿의 {sentence} 부분을 실제 문장으로 교체)
            completed_prompt = prompt_template.format(sentence=sentence)
            
            logger.info(f"{language} 프롬프트 로드 완료")
            return completed_prompt
            
        except Exception as e:
            logger.error(f"프롬프트 파일 읽기 실패 ({language}): {e}")
            raise
    
    def get_supported_languages(self) -> list:
        """지원하는 언어 목록 반환"""
        return list(self.language_files.keys())
    
    def validate_prompts_directory(self) -> bool:
        """프롬프트 디렉토리와 파일들이 존재하는지 확인"""
        if not self.prompts_dir.exists():
            logger.error(f"프롬프트 디렉토리가 존재하지 않습니다: {self.prompts_dir}")
            return False
        
        missing_files = []
        for language, filename in self.language_files.items():
            file_path = self.prompts_dir / filename
            if not file_path.exists():
                missing_files.append(f"{language}: {filename}")
        
        if missing_files:
            logger.error(f"누락된 프롬프트 파일들: {missing_files}")
            return False
        
        logger.info("모든 프롬프트 파일이 정상적으로 존재합니다.")
        return True


# 싱글톤 인스턴스 생성 (모듈 레벨에서 재사용)
prompt_loader = PromptLoader()


def load_prompt_for_language(language: str, sentence: str) -> str:
    """
    편의 함수: 지정된 언어의 프롬프트를 로드
    
    Args:
        language (str): 언어 코드
        sentence (str): 분석할 문장
        
    Returns:
        str: 완성된 프롬프트
    """
    return prompt_loader.load_prompt(language, sentence)


def get_supported_languages() -> list:
    """편의 함수: 지원하는 언어 목록 반환"""
    return prompt_loader.get_supported_languages()


if __name__ == "__main__":
    # 테스트 코드
    loader = PromptLoader()
    
    # 프롬프트 디렉토리 검증
    if loader.validate_prompts_directory():
        print("✅ 프롬프트 파일 검증 완료")
        
        # 각 언어별 테스트
        test_sentence = "Hello world"
        for lang in loader.get_supported_languages():
            try:
                prompt = loader.load_prompt(lang, test_sentence)
                print(f"✅ {lang} 프롬프트 로드 성공 (길이: {len(prompt)})")
            except Exception as e:
                print(f"❌ {lang} 프롬프트 로드 실패: {e}")
    else:
        print("❌ 프롬프트 파일 검증 실패")
