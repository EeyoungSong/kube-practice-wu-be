import openai
import os
import logging
import traceback
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from .prompt_loader import load_prompt_for_language

load_dotenv()
logger = logging.getLogger(__name__)

# Pydantic 모델로 JSON 구조 강제
class WordAnalysis(BaseModel):
    original_text: str
    text: str
    meaning: str
    pos: Optional[str] = None  # 품사 (part of speech)
    others: Optional[str] = None  # 중국어의 경우 병음

class SentenceAnalysis(BaseModel):
    text: str
    meaning: str
    words: List[WordAnalysis]

def call_gpt_for_sentence(sentence, language='english', max_retries=3):
    """
    문장을 분석하여 JSON 형태로 반환하는 함수
    
    Args:
        sentence (str): 분석할 문장
        language (str): 언어 코드 ('english', 'chinese', 'spanish')
        max_retries (int): 최대 재시도 횟수
        
    Returns:
        dict: 분석 결과 또는 None (실패 시)
    """
    # 환경변수 또는 settings에서 OPENAI_API_KEY를 불러오세요.
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    # 입력 문장의 따옴표 전처리
    sentence = sentence.replace('"', '\\"').replace("'", "\\'")
    logger.info(f"전처리된 문장: {sentence}")
    
    for attempt in range(max_retries):
        logger.info(f"시도 {attempt + 1}/{max_retries}")
        
        try:
            # 프롬프트 로더를 사용하여 언어별 프롬프트 로드
            prompt = load_prompt_for_language(language, sentence)
            logger.info(f"{language} 문장 분석: {sentence}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"프롬프트 로드 실패: {e}")
            return None
        
        try:
            logger.info(f"GPT API 호출")
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # 올바른 모델명으로 수정
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # 더 일관된 출력을 위해 낮춤
                max_tokens=5000,  # 긴 문장과 많은 단어를 위해 증가
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            logger.info(f"GPT 원시 응답: {content}")
            
            import re, json
            # response_format으로 JSON을 강제했으므로 전체 content를 JSON으로 파싱
            try:
                parsed_json = json.loads(content)
                logger.info(f"JSON 파싱 성공: {parsed_json}")
                
                # Pydantic 모델로 유효성 검사
                validated_data = SentenceAnalysis(**parsed_json)
                logger.info(f"JSON 구조 검증 성공")
                return validated_data.dict()
                
            except ValidationError as e:
                logger.error(f"시도 {attempt + 1} - JSON 구조 검증 실패: {e}")
                if attempt == max_retries - 1:  # 마지막 시도
                    logger.error(f"검증 실패한 데이터: {parsed_json}")
                continue  # 다음 시도로
                
            except json.JSONDecodeError as e:
                logger.error(f"시도 {attempt + 1} - JSON 파싱 실패: {e}")
                if attempt == max_retries - 1:  # 마지막 시도
                    logger.error(f"문제가 된 JSON: {content}")
                continue  # 다음 시도로
                
        except Exception as e:
            logger.error(f"시도 {attempt + 1} - GPT API 오류: {e}")
            if attempt == max_retries - 1:  # 마지막 시도
                traceback.print_exc()
            continue  # 다음 시도로
    
    # 모든 시도 실패
    logger.error(f"모든 시도 실패: {sentence}")
    return None
    

if __name__ == "__main__":
    sentence = "As of now, the ultimate model for most businesses"
    result = call_gpt_for_sentence(sentence)
    print(result)