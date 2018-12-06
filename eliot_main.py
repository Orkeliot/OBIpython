from typing import *


class ORF:
    """Open Reading Frame defined by start and stop nucleotide"""

    def __init__(self, start: int, stop: int, frame: int, protein: str = "xxx", product: str = "xxx",
                 name: str = "unknown"):
        self.start = start
        self.stop = stop

        self.frame = frame
        self.protein = protein
        self.length = abs(self.stop - self.start)
        self.product = product
        self.name = name

    def __len__(self):
        return self.length

    def __repr__(self):
        return "{:2} : {:10}..{:<10}. {:7} --> {}".format(self.frame, self.start, self.stop, self.name, self.product)


def find_orf(seq: str, threshold: int, code_table_id: int) -> [ORF]:
    """Give a list of all ORF in the sequence if they are grater than the threshold

            This function is written by Eliot Ragueneau.

            Args:
                seq: Sequence source
                threshold: Minimum size of the ORF in the list
                code_table_id: NCBI identifier of the translation table used on this sequence

            Returns:
                list of ORF
        """
    transl_table, start_table = get_genetic_code(code_table_id)

    length = len(seq)
    strands = {1: seq, -1: reversed_complement(seq)}
    orf_list = []
    for strand in strands:
        inits = []
        for i in range(len(strands[strand])):
            if strands[strand][i:i + 3] in start_table:
                inits.append(i)
        # list_stop = []  # Seulement pour n'avoir que les ORFs maximum
        for init in inits:
            prot = "M"
            for i in range(init + 3, len(strands[strand]), 3):
                codon = strands[strand][i: i + 3]
                if len(codon) == 3:
                    aa = transl_table[codon]
                    if aa == "*":
                        if i - init > threshold:  # and i not in list_stop:  Seulement pour n'avoir que les ORFs maximum
                            # list_stop.append(i)
                            if strand > 0:
                                init += 1
                                orf_list.append(ORF(start=init,
                                                    stop=i + 3,
                                                    frame=init % 3 + 1,
                                                    protein=prot))
                            else:
                                orf_list.append(ORF(start=length - (i + 2),
                                                    stop=length - init,
                                                    frame=-1 * ((init - 1) % 3 + 1),
                                                    protein=prot))
                            break
                        else:
                            break
                    prot += aa

    return orf_list


def get_genetic_code(ncbi_id: int) -> Tuple[dict, dict]:
    """Give the initiation codons and the translation table by its id

            This function is written by Eliot Ragueneau.

            Args:
                ncbi_id: ncbi translation table identifier

            Returns:
                transl_table: translating dictionary
                start_table: list of start codons
        """
    with open("Translation_tables/{}.txt".format(ncbi_id), "r") as file:
        lines = [line.strip() for line in file.readlines()]
        transl_table = {lines[2][i] + lines[3][i] + lines[4][i]: lines[0][i]
                        for i in range(len(lines[0]))}
        start_table = {lines[2][i] + lines[3][i] + lines[4][i]: lines[1][i]
                       for i in range(len(lines[0])) if lines[1][i] == "M"}
        return transl_table, start_table


def get_lengths(orf_list: list) -> [int]:
    """Give the list of orf lengths from a list of orf

        This function is written by Eliot Ragueneau.

        Args:
            orf_list: list of ORF.

        Returns:
            list of lengths of ORF
        """
    return [len(orf) for orf in orf_list]


def get_longest_orf(orf_list: List[ORF]) -> ORF:
    """Give the longest orf from a list of orf

            This function is written by Eliot Ragueneau.

            Args:
                orf_list: list of ORF.

            Returns:
                longest ORF
        """
    return max(orf_list, key=lambda orf: len(orf))


def get_top_longest_orf(orf_list: List[ORF], value: float) -> [ORF]:
    """Return the value% top longest orfs from a list of orf

            This function is written by Eliot Ragueneau.

            Args:
                orf_list: list of ORF.
                value: 0 > float > 1 : % of the top longest orf to show

            Returns:
                list of top ORF
        """
    orf_list.sort(key=lambda orf: len(orf))
    return orf_list[int(- value * len(orf_list)) - 1:]


def reversed_complement(dna_seq: str):
    """Return the reversed complement of the given DNA sequence

            This function is written by Eliot Ragueneau.

            Args:
                dna_seq: DNA sequence to be reversed.

            Returns:
                reversed complement DNA sequence
        """
    complement_dict = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join([complement_dict[i] for i in dna_seq[::-1]])


def read_csv(filename: str, separator: str = ";") -> [dict]:
    with open(filename, 'r') as file:
        list_lines = [line.strip() for line in file.readlines()]
        keys = list_lines[0].split(separator)
        return [{key: element for key in keys for element in line.split(separator)} for line in list_lines[1:]]


def write_csv(filename: str, data: list, separator: str = ";"):
    if isinstance(data[0], ORF):
        data = [orf.as_dict() for orf in data]
    filename += ".csv" if filename[-4:] != ".csv" else ""
    with open(filename, "w") as file:
        file.write("{}\n".format(separator.join(data[0])))  # Write only the keys
        for dictionary in data:
            file.write("{}\n".format(separator.join([str(dictionary[key]) for key in dictionary])))


class GenBank:
    """GenBank data structure (More interesting than dictionaries)"""

    def __init__(self, filename: str):
        """Parse a GenBank file

                    This function is written by .

                    Args:
                        filename: .gb file to parse

                    Returns:
                        list of ORF (either as ORF or as dict)
                """
        text = self.read_flat_file(filename)
        list_lines = text.split('\n')
        features = self.get_features(text)
        for line in list_lines:
            if line[:12] == "DEFINITION  ":
                self.description = line[12:]
            elif line[:12] == "VERSION     ":
                self.id = line[12:]
            elif line[:12] == "SOURCE      ":
                self.organism = line[12:]
            elif line[:21] == "     source          ":
                self.length = int(line.split('..')[1])
            elif line[:31] == '                     /mol_type=':
                self.gbtype = line.split('"')[1]
                if "DNA" in self.gbtype:
                    self.type = "dna"
                elif "RNA" in self.gbtype:
                    self.type = "rna"
                # Problème pour les protéines : pas de mol_type dans le cas de protéines
            elif line[:34] == "                     /transl_table":
                self.code_table_id = int(line.split("=")[-1])
                break

        self.genes = self.get_genes(features)

        for i in range(len(list_lines) - 1, -1, -1):
            if list_lines[i][:6] == "ORIGIN":
                self.data = ''.join([''.join(line.split(' ')[-6:]) for line in list_lines[i + 1: -3]])

                break
            elif i == 0:
                self.data = "xxx"

    def show_genes(self):
        for orf in self.genes:
            print(orf)

    @staticmethod
    def read_flat_file(filename: str) -> str:
        """Load a file in memory by returning a string

                This function is written by .

                Args:
                    filename: file to open

                Returns:
                    string of the whole file (with \n)
            """
        with open(filename, 'r') as file:
            return file.read()

    @staticmethod
    def get_features(txt: str) -> str:
        """Extract features lines from flat text and return them

                This function is written by .

                Args:
                    txt: flat text with features to extract

                Returns:
                    string of features
            """
        ls = txt.split('\n')
        for i in range(len(ls)):
            if ls[i][:8] == "FEATURES":
                return '\n'.join([x[5:] for x in ls[i + 1:]])

    def get_genes(self, features: str) -> [ORF]:
        """Extract gene and CDS data from their section inside features table

                This function is written by .

                Args:
                    features: text with gene to extract

                Returns:
                    list of ORF (either as ORF or as dict)
            """
        ls = features.split('\n')
        cds_begins, cds_begins, cds_ends, list_cds, list_orf = [], [], [], [], []
        cds = False

        for i in range(len(ls)):  # Récupération des positions des différentes entrées CDS
            classe = ls[i][:3]
            if classe == "CDS":
                cds = True
                cds_begins.append(i)
            elif classe != "   " and cds:
                cds = False
                cds_ends.append(i)

        for i in range(len(cds_begins)):  # Récupération des CDS depuis leurs positions dans le fichier
            list_cds.append(ls[cds_begins[i]: cds_ends[i]])

        for cds in list_cds:  # Création de la liste d'ORF à partir de la liste de CDS du fichier gb
            if cds[0][16:26] == "complement":
                pos = cds[0][27:].split('..')
                start = int(pos[0])
                stop = int(pos[1].strip(')'))
                frame = -((self.length - start) % 3 + 1)
            else:
                pos = [int(x) for x in cds[0][16:].split('..')]
                start = int(pos[0])
                stop = int(pos[1])
                frame = (start % 3) + 1
            name = "unknown"
            protein = "xxx"
            product = "xxx"
            for i in range(1, len(cds)):
                line = cds[i][16:]
                if "/gene" == line[:5]:
                    name = ''.join([x[16:] for x in cds[i:]]).split('"')[1]
                elif "/product" == line[:8]:
                    product = ''.join([x[16:] for x in cds[i:]]).split('"')[1]
                elif "/translation" == line[:12]:
                    protein = ''.join([x[16:] for x in cds[i:]]).split('"')[1]
                    break
            list_orf.append(ORF(start, stop, frame, protein, product, name))

        return list_orf

    @staticmethod
    def read(filename):
        """Parse a GenBank file

                This function is written by .

                Args:
                    filename: .gb file to parse

                Returns:
                    list of ORF (either as ORF or as dict)
            """
        return GenBank(filename)

    def __repr__(self):
        return "{} : {} of {}".format(self.id, self.gbtype, self.organism)


def read_fasta(filename: str) -> str:
    dna = ""
    with open(filename, 'r') as fasta:
        for fasta_line in fasta:
            if fasta_line[0] != ">":
                dna += fasta_line.strip()
    return dna


def translate(seq):
    transl_table, start_table = get_genetic_code(11)
    prot = "M"
    for i in range(3, len(seq), 3):
        codon = seq[i: i + 3]
        if len(codon) == 3:
            aa = transl_table[codon]
            prot += aa
    return prot


def complement(seq):
    complement_dict = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join([complement_dict[i] for i in seq])


if __name__ == '__main__':
    genome = read_fasta("influenza.fasta")
    # list_orf = find_orf(genome, 89, 11)
    # for orf in list_orf:
    #     print(orf.protein)

    influenza = GenBank("sequence.gb")
    # list_prot = [str(x) for x in list_orf]
    for gene in influenza.genes:
        print(gene)
        # if str(gene) not in list_prot:
        #     print(gene)
