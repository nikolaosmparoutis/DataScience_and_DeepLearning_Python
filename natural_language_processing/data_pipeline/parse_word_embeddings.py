import os
import numpy as np

"""ParseWordEmbeddings is a pretrained  network. A saved network that was previously
trained on a large dataset.If this original dataset is large enough and general enough
the hierarchy of features learned by the pretrained network can effectively act as 
a generic model.But for very specific tasks word embeddings make things worse.
It is flexible to experiment with and without Embeddings, for fine tuning - unfreezing a few of
the top layers of the frozen model, which hold the more abstract patterns.We do this in order 
to make them more relevant for the problem at hand, to improve the accuracy.
"""

from natural_language_processing.configurations.configuration_infrastructure import Config
from natural_language_processing.configurations.configurations import CFG
from natural_language_processing.logging.LoggerCls import LoggerCls
import natural_language_processing.utils.time_counter as run_time
import os.path


class ParseWordEmbeddings:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    formatter = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logToFile = LoggerCls("log_to_file", "data pipeline processor:",
                          dir_path + "/data_pipeline.log", "w", formatter,
                          "INFO")
    logToStream = LoggerCls("log_to_stdout", "data pipeline processor: ", None, "w", formatter, "INFO")

    def __init__(self):
        self.config = Config.from_json(CFG)
        self.dir_embeddings_data = self.config.external_data_sources.word_embeddings
        self.file_name = self.config.external_data_sources.embeddings_file_name

    @run_time.timer
    def embeddings_vectors(self):
        """  Embeddings is a dictionary that maps the word indices to an associated vector."""
        try:
            embedding_indexed_vectors = {}
            with open(os.path.join(self.dir_embeddings_data, self.file_name)) as f:
                for line in f:
                    values = line.split()
                    word = values[0]
                    coefs = np.asarray(values[1:], dtype='float32')
                    # a list consists a word and all the weights (coefs) computed from the NN
                    embedding_indexed_vectors[word] = coefs
            ParseWordEmbeddings.logToStream.info("Found %s coefficients." % len(coefs))
            ParseWordEmbeddings.logToStream.info("Found %s word vectors." % len(embedding_indexed_vectors))
            return embedding_indexed_vectors
        except (IOError, FileNotFoundError, TypeError, Exception) as e:
            ParseWordEmbeddings.logToFile.logger.error("Error encountered on method <embeddings_vectors>")
            ParseWordEmbeddings.logToFile.logger.error(e)


    @classmethod
    @run_time.timer
    def create_embeddings_matrix(self, word_index):
        """ All sequences in a batch must have the same length to pack them in a single tensor
        so we do zero padding to shorter the sequences where the longer sequences are truncated."""

        ParseWordEmbeddings.logToStream.logger.info("Create embeddings matrix.")
        try:
            max_words = self.config.data.max_words
            embedding_matrix = np.zeros((max_words,
                                         self.config.external_data_sources.embeddings_dimension))
            embedding_indexed_vectors = self.embeddings_vectors()
            for word, i in word_index.items():
                if i < max_words:
                    embedding_vector = embedding_indexed_vectors.get(word)
                    if embedding_vector is not None:  # if words not found in the embedding index will be zeros
                        embedding_matrix[i] = embedding_vector
            return embedding_matrix

        except Exception as e:
            ParseWordEmbeddings.logToFile.logger.error("Error in <create_embeddings_matrix>")
            ParseWordEmbeddings.logToFile.logger.error(e)

    @classmethod
    @run_time.timer
    def store_h5py(self, embedding_matrix):
        ParseWordEmbeddings.logToStream.logger.info("Stores to compressed file")
        try:
            from h5py import File
            hdf = File(ParseWordEmbeddings.config.external_data_sources.HDFS_EXTERNAL_DATA_FILENAME, "w")
        except IOError as e:
            ParseWordEmbeddings.logToFile.logger.error("Error encountered in method <store h5py>. \
            The external file failed to open for write")
            ParseWordEmbeddings.logToFile.logger.error(e)
        else:
            hdf.create_dataset("external_dataset", data=embedding_matrix, compression="gzip")
            hdf.close()
            # ParseWordEmbeddings.logToFile.logger.info("Successful creation of file with embeddings.")
            ParseWordEmbeddings.logToStream.logger.info("Successful creation of file with embeddings.")
