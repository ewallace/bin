#!/usr/bin/env python
desc="""Identify SNP sites in mpileup out from BAM alignments. 
 
CHANGELOG:
+ 1.1:
- mpileup options added
"""
epilog="""Author:
l.p.pryszcz@gmail.com

Barcelona, 28/06/2012
"""

import argparse, os, sys
from datetime import datetime
import subprocess

def _remove_indels( alts ):
    """
    Remove indels from mpileup.
    .$....,,,,....,.,,..,,.,.,,,,,,,....,.,...,.,.,....,,,........,.A.,...,,......^0.^+.^$.^0.^8.^F.^].^],
    ........,.-25ATCTGGTGGTTGGGATGTTGCCGCT..
    """
    #remove indels info
    for symbol in ('-','+'):
        baseNo = 0
        while symbol in alts:
            i=alts.index(symbol)
      
            j = 1
            digits=[]
            while alts[i+j].isdigit():
                digits.append( alts[i+j] )
                j += 1
      
            if digits:
                baseNo=int( ''.join(digits) )
        
            alts=alts[:i]+alts[i+baseNo+len(digits)+1:] #......+1A..,
      
    return alts

def get_alt_allele(base_ref, cov, alg, minFreq, alphabet, reference, bothStrands):
    """Return alternative allele only if different than ref and freq >= minFreq."""
    #remove deletions
    alts = alg
    dels = alts.count('*') 
    #remove insertions
    alts = _remove_indels( alts )
    #get base counts
    baseCounts = [(alts.upper().count(base), base) for base in alphabet]
    #get base frequencies
    for base_count, base in sorted(baseCounts):
        freq = base_count*1.0/cov
        if base!=base_ref and freq >= minFreq:
            #check if alt base in both strands
            if bothStrands: 
                if not base.upper() in alts or not base.lower() in alts:
                    return
            return (base, freq) # base!=base_ref and

def get_major_alleles(cov, alg, minFreq, alphabet, bothStrands):
    """Return major alleles that passed filtering and their frequencies."""
    #remove deletions
    alts = alg
    dels = alts.count('*') 
    #remove insertions
    alts = _remove_indels( alts )
    #get base frequencies
    bases, freqs = set(), []
    for base_count, base in zip((alts.upper().count(b) for b in alphabet), alphabet):
        freq = base_count*1.0/cov
        #check freq
        if freq < minFreq:
            continue
        #check if alt base in both strands
        if bothStrands: 
            if not base.upper() in alts or not base.lower() in alts:
                continue
        bases.add(base)
        freqs.append(freq)
    return bases, freqs
  
def parse_mpileup(fnames, fastaFn, minDepth, minFreq, indels, mpileup_opts,\
                  no_reference, bothStrands, verbose, alphabet='ACGT'):
    """Run mpileup subprocess and parse output."""
    # open out files and write header
    header = '#coordinate\treference coverage\tref base\tref freq\talt coverage\talt base\talt freq\n'
    outline = '%s:%s\t%s\t%s\t%1.4f\t%s\t%s\t%1.4f\n'
    fi = 1
    if no_reference:
        fi = 0
    fnbase = "%s.snps.cov_%s.freq_%s.bothStrands_%s.txt"
    outFiles = [open(fnbase%(fn, minDepth, minFreq, bothStrands), "w") for fn in fnames[fi:]]
    for out in outFiles:
        out.write(header)
    
    #process mpileup
    contigs=[]
    totCov={}; totLen={}; pContig=pPos=0
    #open subprocess
    args = ['samtools', 'mpileup'] + mpileup_opts.split() + fnames #; print args
    if verbose:
        sys.stderr.write("Running samtools mpileup...\n %s\n" % " ".join(args))
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=65536)
    for line in proc.stdout:
        line      = line.strip()
        lineTuple = line.split('\t')
        #get coordinate
        contig, pos, baseRef = lineTuple[:3]
        if no_reference:
            refCov = 0
            baseRef, refFreq = [baseRef], [1.0]
            samplesData = lineTuple[3:]
        #laod ref data
        else:
            refCov, refAlgs, refQuals = lineTuple[3:6]
            refCov = int(refCov)
            samplesData = lineTuple[6:]
            if refCov < minDepth:
                continue
            baseRef, refFreq = get_major_alleles(refCov, refAlgs, minFreq, alphabet, bothStrands)
            if not baseRef:
                continue
            
        for out, cov, alg, quals in zip(outFiles, samplesData[0::3], samplesData[1::3], samplesData[2::3]):
            cov=int(cov)
            if cov<minDepth:
                continue
            # check for SNP
            bases, freqs = get_major_alleles(cov, alg, minFreq, alphabet, bothStrands)
            if not bases or bases==baseRef:
                continue
<<<<<<< HEAD
            # get base and freq
            base,freq = alt_allele

            lineOut='%s:%s\t%s\t%s\t%1.4f\t%s\t%s\t%1.4f\n' % (contig, pos, refCov, baseRef, refFreq, cov, base, freq)
            out.write( lineOut )
=======
            out.write(outline%(contig, pos, refCov, ",".join(baseRef), max(refFreq), \
                               cov, ",".join(bases), max(freqs)))
>>>>>>> 4e683bd8f4fd2ee01b4d6c249a6b93ff5f238982
            if verbose:
                print outline%(contig, pos, refCov, ",".join(baseRef), max(refFreq), \
                               cov, ",".join(bases), max(freqs)),
  
    for out in outFiles:  
        out.close()

def main():

    usage  = "%(prog)s [options] -b ref.bam *.bam" 
    parser  = argparse.ArgumentParser(usage=usage, description=desc, epilog=epilog, \
                                      formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="verbose")    
    parser.add_argument('--version', action='version', version='1.1')
    parser.add_argument("-b", "--bam", nargs="+", 
                        help="input BAM files, first one should be reference bam")
    parser.add_argument("-i", "--fasta", 
                        help="fasta [required only if no reference bam]")
    parser.add_argument("-d", "--minDepth", default=5,  type=int,
                        help="minimal depth                     [%(default)s]")
    parser.add_argument("-f", "--minFreq",  default=0.8, type=float,
                        help="min frequency of alternative base [%(default)s]")
    parser.add_argument("--mpileup_opts",   default="-q 15 -Q 20",  
                        help="options passed to mpileup         [%(default)s]")
    parser.add_argument("-n", "--indels",   default=False, action="store_true", 
                        help="report indels")
    parser.add_argument("--bothStrands",    default=False, action="store_true", 
                        help="only SNP confirmed by both strand algs")
    parser.add_argument("--no_reference",   default=False, action="store_false", 
                        help="first bam IS NOT reference")
  
    o = parser.parse_args()
    if o.verbose:
        sys.stderr.write("Options: %s\n"%str(o))
    
    #parse pileup
    parse_mpileup(o.bam, o.fasta, o.minDepth, o.minFreq, o.indels, o.mpileup_opts, \
                  o.no_reference, o.bothStrands, o.verbose)
    
if __name__=='__main__': 
    t0 = datetime.now()
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\nCtrl-C pressed!      \n")
    except IOError as e:
        sys.stderr.write("I/O error({0}): {1}\n".format(e.errno, e.strerror))
    dt = datetime.now()-t0
    sys.stderr.write("#Time elapsed: %s\n" % dt)
