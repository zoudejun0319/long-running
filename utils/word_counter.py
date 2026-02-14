"""
字数统计工具模块
"""

import re
from typing import Dict, List


class WordCounter:
    """字数统计器，支持中英文混合"""

    # 中文字符范围
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]')
    # 英文单词模式
    ENGLISH_PATTERN = re.compile(r'[a-zA-Z]+')
    # 数字模式
    NUMBER_PATTERN = re.compile(r'[0-9]+')

    @staticmethod
    def count(text: str) -> Dict[str, int]:
        """
        统计文本字数
        返回: {
            'chinese': 中文字数,
            'english': 英文单词数,
            'numbers': 数字数,
            'total': 总字数（中文字符 + 英文单词）
        }
        """
        chinese_chars = len(WordCounter.CHINESE_PATTERN.findall(text))
        english_words = len(WordCounter.ENGLISH_PATTERN.findall(text))
        numbers = len(WordCounter.NUMBER_PATTERN.findall(text))

        # 对于中文小说，主要统计中文字符
        # 英文单词按1个单位计算
        total = chinese_chars + english_words

        return {
            'chinese': chinese_chars,
            'english': english_words,
            'numbers': numbers,
            'total': total
        }

    @staticmethod
    def count_chinese_only(text: str) -> int:
        """仅统计中文字符数"""
        return len(WordCounter.CHINESE_PATTERN.findall(text))

    @staticmethod
    def is_within_range(text: str, min_words: int, max_words: int) -> Dict:
        """
        检查字数是否在范围内
        返回: {
            'in_range': bool,
            'actual': int,
            'min': int,
            'max': int,
            'difference': int  # 与最小值的差距（正数表示超出）
        }
        """
        count = WordCounter.count(text)
        actual = count['total']
        in_range = min_words <= actual <= max_words

        return {
            'in_range': in_range,
            'actual': actual,
            'min': min_words,
            'max': max_words,
            'difference': actual - min_words
        }

    @staticmethod
    def analyze_chapters(chapter_texts: List[Dict[str, str]]) -> Dict:
        """
        分析多个章节的字数统计
        输入: [{'chapter': 1, 'text': '...'}, ...]
        """
        results = []
        total_words = 0

        for item in chapter_texts:
            count = WordCounter.count(item['text'])
            results.append({
                'chapter': item.get('chapter', 0),
                'title': item.get('title', ''),
                **count
            })
            total_words += count['total']

        return {
            'chapters': results,
            'total_words': total_words,
            'average_per_chapter': total_words / len(chapter_texts) if chapter_texts else 0,
            'chapter_count': len(chapter_texts)
        }

    @staticmethod
    def get_statistics(text: str) -> Dict:
        """获取详细统计信息"""
        count = WordCounter.count(text)

        # 额外统计
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s for s in sentences if s.strip()]

        return {
            **count,
            'paragraphs': len(paragraphs),
            'sentences': len(sentences),
            'avg_sentence_length': count['total'] / len(sentences) if sentences else 0
        }
