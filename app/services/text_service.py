import pandas as pd
from typing import List, Dict, Any
import requests
from app.core.config import settings


class TextAnalysisService:
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
    
    def summarize_text(self, text: str, max_length: int = 100) -> str:
        try:
            prompt = f"Summarize the following text in {max_length} characters or less:\n\n{text}\n\nSummary:"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": max_length
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            summary = response.json()['response'].strip()
            return summary
        except:
            if len(text) > max_length:
                return text[:max_length] + "..."
            return text
    
    def classify_sentiment(self, text: str) -> str:
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful',
            'fantastic', 'awesome', 'satisfied', 'happy', 'love',
            'best', 'perfect', 'outstanding', 'pleased', 'impressed'
        ]
        negative_words = [
            'bad', 'poor', 'terrible', 'awful', 'horrible',
            'disappointed', 'worst', 'hate', 'useless', 'waste',
            'defective', 'broken', 'failure', 'unacceptable', 'frustrating'
        ]
        
        text_lower = str(text).lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        text_lower = str(text).lower()
        
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        words = text_lower.split()
        word_freq = {}
        
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if word and word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def analyze_text_column(self, df: pd.DataFrame, column: str, analysis_type: str) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")
        
        if analysis_type == 'sentiment':
            df['sentiment'] = df[column].apply(self.classify_sentiment)
        elif analysis_type == 'summary':
            df['summary'] = df[column].apply(lambda x: self.summarize_text(str(x), 100))
        elif analysis_type == 'keywords':
            df['keywords'] = df[column].apply(lambda x: ', '.join(self.extract_keywords(str(x))))
        elif analysis_type == 'length':
            df['text_length'] = df[column].apply(lambda x: len(str(x)))
        elif analysis_type == 'word_count':
            df['word_count'] = df[column].apply(lambda x: len(str(x).split()))
        
        return df
    
    def batch_summarize(self, texts: List[str], max_length: int = 100) -> List[str]:
        summaries = []
        for text in texts:
            summary = self.summarize_text(text, max_length)
            summaries.append(summary)
        return summaries
    
    def categorize_text(self, text: str, categories: List[str]) -> str:
        text_lower = str(text).lower()
        
        category_keywords = {
            'complaint': ['complaint', 'issue', 'problem', 'broken', 'not working', 'defective'],
            'inquiry': ['how', 'what', 'when', 'where', 'question', 'help', 'information'],
            'feedback': ['feedback', 'suggestion', 'recommend', 'improve', 'feature'],
            'praise': ['thank', 'thanks', 'great', 'excellent', 'love', 'appreciate'],
            'technical': ['error', 'bug', 'crash', 'code', 'technical', 'api', 'install']
        }
        
        scores = {}
        for category in categories:
            cat_lower = category.lower()
            if cat_lower in category_keywords:
                keywords = category_keywords[cat_lower]
                score = sum(1 for keyword in keywords if keyword in text_lower)
                scores[category] = score
            else:
                scores[category] = 1 if cat_lower in text_lower else 0
        
        if max(scores.values()) == 0:
            return 'other'
        
        return max(scores, key=scores.get)