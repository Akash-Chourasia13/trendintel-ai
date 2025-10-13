import re
from transformers import pipeline
from keybert import KeyBERT
from thefuzz import fuzz
import spacy

nlp = spacy.load("en_core_web_sm")


class ReviewAnalyzer:
    def __init__(self):
        # self.sentiment_analyzer = pipeline('sentiment-analysis')
        self.sentiment_analyzer = pipeline(
            'sentiment-analysis',
            model='distilbert/distilbert-base-uncased-finetuned-sst-2-english'
        )
        self.summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
        self.keyword_extractor = KeyBERT()
        self.aspect_model = pipeline("text-classification", model="yangheng/deberta-v3-base-absa-v1.1")

        # Define common cloth product aspects
        self.aspects = ["fit", "fabric", "material", "color", "stitch", "stitching",
                        "delivery", "price", "comfort", "size", "design", "thread"]

    def clean_text(self, text):
        return re.sub(r"\s+", " ", text.strip())
    
    def get_overall_sentiment(self,text):
        result = self.sentiment_analyzer(text[:512])[0]
        return {'label':result['label'].lower(),"score":round(result['score'],3)*100}

    def get_summary(self, text):
        if len(text.split()) < 30:
            return text
        result = self.summarizer(text, max_length=60, min_length=20, do_sample=False)
        return result[0]['summary_text']

        
    def get_keywords(self,text):
        return [kw[0] for kw in self.keyword_extractor.extract_keywords(text,top_n=3)]

    def get_aspect_sentiments(self,text):
        aspect_sentiments = {}
        doc = nlp(text.lower())
        tokens = [token.lemma_ for token in doc]      

        for aspect in self.aspects:
            matched_positions = []
            for i,token in enumerate(tokens):      
                if token == aspect:
                    matched_positions.append(i)
                elif len(aspect) > 4 and fuzz.ratio(token, aspect) >= 80:
                    matched_positions.append(i)
    
            for idx in matched_positions:
                start = max(0,idx-10)
                end = min(len(tokens),idx+10)
                snippet = " ".join(tokens[start:end])
                result = self.aspect_model(f"[ASPECT] {aspect} [TEXT] {snippet}")[0]

                if aspect not in aspect_sentiments:
                    aspect_sentiments[aspect] = []
                aspect_sentiments[aspect].append({
                    'label':result['label'].lower(),
                    'confidence': round(result['score'],3)*100,
                    'context':snippet
                })       
        return aspect_sentiments   
    def analyze(self, review_text):
        text = self.clean_text(review_text)
        if not text:
            return None
        return {
            "overall_sentiment": self.get_overall_sentiment(text),
            "summary": self.get_summary(text),
            "keywords": self.get_keywords(text),
            "aspect_sentiments": self.get_aspect_sentiments(text)
        }
                                    