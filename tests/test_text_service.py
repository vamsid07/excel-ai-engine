import pytest
import pandas as pd
from unittest.mock import Mock, patch
from app.services.text_service import TextAnalysisService
import requests


class TestTextAnalysisService:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = TextAnalysisService()
    
    def test_init(self):
        assert self.service.ollama_url is not None
        assert self.service.model is not None
    
    def test_classify_sentiment_positive(self):
        text = "Great product! Love it and very satisfied"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'positive'
    
    def test_classify_sentiment_negative(self):
        text = "Terrible experience. Worst product ever and disappointed"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'negative'
    
    def test_classify_sentiment_neutral(self):
        text = "The product arrived on time"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'neutral'
    
    def test_classify_sentiment_mixed_positive_wins(self):
        text = "Great excellent wonderful but one bad thing"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'positive'
    
    def test_classify_sentiment_mixed_negative_wins(self):
        text = "Good but terrible awful and worst ever"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'negative'
    
    def test_classify_sentiment_empty(self):
        text = ""
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'neutral'
    
    def test_extract_keywords_basic(self):
        text = "Python programming language is great for data analysis and machine learning"
        
        keywords = self.service.extract_keywords(text, top_n=3)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 3
        assert all(isinstance(k, str) for k in keywords)
    
    def test_extract_keywords_filters_stop_words(self):
        text = "The the the and and or but in on at to for"
        
        keywords = self.service.extract_keywords(text, top_n=5)
        
        assert len(keywords) == 0
    
    def test_extract_keywords_frequency_sorting(self):
        text = "python python python java java javascript"
        
        keywords = self.service.extract_keywords(text, top_n=3)
        
        assert keywords[0] == 'python'
    
    def test_extract_keywords_minimum_length(self):
        text = "a be cat dog elephant"
        
        keywords = self.service.extract_keywords(text, top_n=5)
        
        assert 'a' not in keywords
        assert 'elephant' in keywords
    
    def test_extract_keywords_alphanumeric_only(self):
        text = "test123 programming! data@analysis #hashtag"
        
        keywords = self.service.extract_keywords(text, top_n=5)
        
        assert all(k.isalnum() for k in keywords)
    
    def test_analyze_text_column_sentiment(self, sample_text_dataframe):
        result_df = self.service.analyze_text_column(
            sample_text_dataframe,
            'customer_feedback',
            'sentiment'
        )
        
        assert 'sentiment' in result_df.columns
        assert all(s in ['positive', 'negative', 'neutral'] for s in result_df['sentiment'])
    
    def test_analyze_text_column_length(self, sample_text_dataframe):
        result_df = self.service.analyze_text_column(
            sample_text_dataframe,
            'customer_feedback',
            'length'
        )
        
        assert 'text_length' in result_df.columns
        assert all(isinstance(x, int) for x in result_df['text_length'])
    
    def test_analyze_text_column_word_count(self, sample_text_dataframe):
        result_df = self.service.analyze_text_column(
            sample_text_dataframe,
            'customer_feedback',
            'word_count'
        )
        
        assert 'word_count' in result_df.columns
        assert all(isinstance(x, int) for x in result_df['word_count'])
    
    def test_analyze_text_column_keywords(self, sample_text_dataframe):
        result_df = self.service.analyze_text_column(
            sample_text_dataframe,
            'customer_feedback',
            'keywords'
        )
        
        assert 'keywords' in result_df.columns
        assert all(isinstance(x, str) for x in result_df['keywords'])
    
    @patch('requests.post')
    def test_analyze_text_column_summary(self, mock_post, sample_text_dataframe):
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': 'This is a summary'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result_df = self.service.analyze_text_column(
            sample_text_dataframe,
            'customer_feedback',
            'summary'
        )
        
        assert 'summary' in result_df.columns
    
    def test_analyze_text_column_invalid_column(self, sample_text_dataframe):
        with pytest.raises(ValueError, match="not found in dataframe"):
            self.service.analyze_text_column(
                sample_text_dataframe,
                'nonexistent_column',
                'sentiment'
            )
    
    @patch('requests.post')
    def test_summarize_text_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': 'Short summary of the text'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = self.service.summarize_text("Long text here", max_length=50)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_text_fallback_on_error(self):
        long_text = "A" * 200
        
        result = self.service.summarize_text(long_text, max_length=50)
        
        assert len(result) <= 53
        assert result.endswith('...')
    
    def test_summarize_text_short_text(self):
        short_text = "Short"
        
        result = self.service.summarize_text(short_text, max_length=100)
        
        assert result == short_text
    
    def test_batch_summarize(self):
        texts = ["Text one", "Text two", "Text three"]
        
        summaries = self.service.batch_summarize(texts, max_length=50)
        
        assert len(summaries) == len(texts)
        assert all(isinstance(s, str) for s in summaries)
    
    def test_categorize_text_complaint(self):
        text = "I have a complaint about the broken product"
        categories = ['complaint', 'inquiry', 'feedback']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'complaint'
    
    def test_categorize_text_inquiry(self):
        text = "How do I use this feature? What is the price?"
        categories = ['complaint', 'inquiry', 'feedback']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'inquiry'
    
    def test_categorize_text_feedback(self):
        text = "I have some feedback and suggestions to improve the product"
        categories = ['complaint', 'inquiry', 'feedback']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'feedback'
    
    def test_categorize_text_praise(self):
        text = "Thank you so much! Great service and excellent support"
        categories = ['complaint', 'inquiry', 'praise']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'praise'
    
    def test_categorize_text_technical(self):
        text = "Error code 500. The API crashed and there is a bug"
        categories = ['complaint', 'technical', 'inquiry']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'technical'
    
    def test_categorize_text_custom_category(self):
        text = "This is about billing issues"
        categories = ['billing', 'shipping', 'returns']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'billing'
    
    def test_categorize_text_no_match(self):
        text = "Random text with no keywords"
        categories = ['category1', 'category2']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'other'
    
    def test_categorize_text_case_insensitive(self):
        text = "COMPLAINT about the PRODUCT"
        categories = ['complaint', 'inquiry']
        
        result = self.service.categorize_text(text, categories)
        
        assert result == 'complaint'
    
    def test_sentiment_with_numbers(self):
        text = "Product rated 5 stars excellent"
        
        result = self.service.classify_sentiment(text)
        
        assert result == 'positive'
    
    def test_keywords_with_duplicates(self):
        text = "data data analysis analysis python programming"
        
        keywords = self.service.extract_keywords(text, top_n=2)
        
        assert len(keywords) == 2
        assert 'data' in keywords or 'analysis' in keywords