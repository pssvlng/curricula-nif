import spacy

class SimilarityClassifier:

    def __init__(self, spacyModel):        
        self.nlp = spacyModel

    def classify(self, text1: str, text2: str) -> float:
        try:
            stop_words = self.nlp.Defaults.stop_words
            list1 = text1.split(' ')
            list2 = text2.split(' ') 
            list1 = [word for word in list1 if word not in stop_words]
            list2 = [word for word in list2 if word not in stop_words]
            doc1 = self.nlp(' '.join(list1))
            doc2 = self.nlp(' '.join(list2))
            return doc1.similarity(doc2)
        except Exception as e:
            print(f'Could not classify: {e}')
            return 0.0
        #     print('')
        #     print(text1)
        #     print('AND')
        #     print('')
        #     print(text2)
        #     return 0.0        

        

    def __repr__(self):
        return 'SimilarityClassifier()'

    def __str__(self):
        return 'SimilarityClassifier()'
