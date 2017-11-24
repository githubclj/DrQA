import json
import codecs
from ultize import *
#训练的时候随便多少个batch都可以，但是在inference的时候要改下
class Reader(object):
    def __init__(self , config, vocab  ):

        source_fp=codecs.open(config.data_path ,'r','utf8')
        # read  datas
        self.data = source_fp.readlines()
        # the whole length of data
        self.length  = len(self.data)
        # load vocab
        self.vocab =  vocab
        # the index of question
        self.question_index = 0
        # the index of passage
        self.passage_index = 0
        # json load buffer
        self.line  = json.loads(self.data[self.question_index])

        self.num_examples = 0

        self.batch_size = config.batch_size

        # see how many examples we have
        for i in range(self.length):
            line = json.loads(self.data[i])['passages']
            for i in range(len(line)):
                if len(line[i]):
                    self.num_examples +=1
        # load pos vocab
        self.pos_vocab  = self._load_pos_vocab(config.pos_vocab_path)

        print(self.num_examples)

    def _load_pos_vocab(self,filename):
        # load pos vocab
        vocab = []
        with codecs.open(filename,'r','utf-8') as fp:
            for line in fp:
                vocab.append(line.strip())

        vocab_index = range(len(vocab))
        vocab = dict(zip(vocab,vocab_index)) # vocab
        return vocab
    def get_batch(self):
        """
        return [batch_size,length]
        """
        batch_query_ls  = []
        passage_ls = []
        answer_ls  = []
        answer_p_s = []
        answer_p_e = []
        passage_pos_ls = []

        patched_index= 0
        while  patched_index < self.batch_size:
            # convert the batch return to id
            query , passage , answer ,answer_p  , passage_pos =  self.next_batch()
            # add </s> to the passage
            passage.append('</s>')

            #perform word2id
            query , passage , answer = self._batch2id( (query , passage , answer))

            # for the pos of </s>       
            passage_pos.append("end")
            #perform pos2id

            passage_pos = self._pos2id(passage_pos)

            # because we add </s> so the len must bigger than 1
            if len(passage) >1:
                # the count of patched data
                patched_index+=1

                batch_query_ls.append(query)
                passage_ls.append(passage)
                answer_ls.append(answer)

                passage_pos_ls.append(passage_pos)
                if answer_p :
                    answer_p_s.append(answer_p[0])
                    answer_p_e.append(answer_p[1]+1) # here we plus 1 because we less 1 in adding answer points
                else:
                    # note here should be the end of the sentence
                    # I add </s> to th end of the passage so we can set None p to the end
                    answer_p_s.append(len(passage) -1)
                    answer_p_e.append(len(passage) -1)
        return  batch_query_ls , passage_ls, answer_ls, answer_p_s, answer_p_e ,passage_pos_ls
    def reset(self):
        self.question_index = 0
        self.line  = json.loads(self.data[self.question_index])
    def next_batch(self):
        # load one json line from file
        # question

        query , _  =   token_pos(self.line['query'])
        # passage
        passage , passage_pos   =  token_pos (self.line['passages'][self.passage_index]['passage_text'] )
        # answer
        answer   =   self.line['answer'].split()
        # answer_point
        answer_p  =  self.line['passages'][self.passage_index]['answer_point']

        self.passage_index +=1

        if self.passage_index  == len(self.line['passages']):
            self.passage_index  = 0
            self.question_index +=1
            if  self.question_index >= self.length:
                self.question_index =0
            # reload json line
            self.line  = json.loads(self.data[self.question_index])
        return   query , passage , answer ,answer_p  , passage_pos
    def _word2id(self,sentence):
        ids = []
        unk_id = self.vocab['<unk>']
        for character in sentence:
            ids.append( self.vocab.get(character,unk_id) )
        return ids
    def _batch2id(self,pair):
        """
        pair: the list of  q,a,d
        vocab:vocab
        """
        q_id,d_id,a_id = [ self._word2id(item) for item in pair]
        return  q_id,d_id,a_id
    def _pos2id(self,ls):
        """
        ls : the list of pos
        return the list of ids
        """
        pos_id =  [ self.pos_vocab.get(item) for item in ls]
        return pos_id

class infe_reader(object):

    def __init__(self , arg , vocab  ):
        source_fp=codecs.open(arg.data_path ,'r','utf8')
        # read  datas
        self.data = source_fp.readlines()
        # the whole length of data
        self.length  = len(self.data)
        # load vocab
        self.vocab =  vocab
        # the index of question
        self.question_index = 0
        # the index of passage
        self.passage_index = 0

        # load pos vocab
        self.pos_vocab  = self._load_pos_vocab(arg.pos_vocab_path)

    def _load_pos_vocab(self,filename):
        # load pos vocab
        vocab = []
        with codecs.open(filename,'r','utf-8') as fp:
            for line in fp:
                vocab.append(line.strip())

        vocab_index = range(len(vocab))
        vocab = dict(zip(vocab,vocab_index)) # vocab
        return vocab

    def get_batch(self):
        """
        return [batch_size,length]
        """
        # return the original passages
        origin_passage = []

        batch_query_ls  = []
        
        passage_ls = []
        
        query_id  = []

        passage_pos_ls = []
        
        # json load buffer
        self.line  = json.loads(self.data[self.question_index])

        for i in range(len(self.line['passages'])):

            # convert the batch return to id
            query, _ = token_pos(self.line['query'])
            # passage
            passage, passage_pos  =  token_pos(self.line['passages'][i]['passage_text'])

            # query id
            q_id =   self.line['query_id']
            # add </s> to the passage
            passage.append('</s>')

            passage_pos.append('end')

            query , id_passage  = self._batch2id( (query , passage ))

            passage_pos = self._pos2id(passage_pos)

            # because we add </s> so the len must bigger than 1
            if len(id_passage) > 1:
                # the count of patched data
                batch_query_ls.append(query)
                passage_ls.append(id_passage)

                origin_passage.append(passage)# this is for inference 
                
                query_id.append(q_id)

                passage_pos_ls.append(passage_pos)

        self.question_index+=1
        if self.question_index > self.length :
            self.question_index = 0
        return  batch_query_ls , passage_ls, query_id,origin_passage,passage_pos_ls
    def reset(self):
        self.question_index = 0
        
    def _word2id(self,sentence):
        ids = []
        unk_id = self.vocab['<unk>']
        for character in sentence:
            ids.append( self.vocab.get(character,unk_id) )
        return ids
    def _batch2id(self,pair):
        """
        pair: the list of  q,a,d
        vocab:vocab
        """
        query_id,passage_id = [ self._word2id(item) for item in pair]
        return  query_id,passage_id

    def _pos2id(self,ls):
        """
        ls : the list of pos
        return the list of ids
        """
        pos_id =  [ self.pos_vocab.get(item) for item in ls]
        return pos_id