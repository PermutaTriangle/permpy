import sys
import os
import subprocess
import time
import math
import random
import fractions
import itertools

# python 2/3 compatibility
from functools import reduce

import permpy.permset

__author__ = 'Cheyne Homberger, Jay Pantone'


# a class for creating permutation objects
class Permutation(tuple):
    """Class for Permutation objects, representing permutations of an ordered
    n-element set. Permutation objects are immutable, and represented internally
    as a n-tuple of the integers 0 through n-1."""

    # static class variable, controls permutation representation
    _REPR = 'oneline'

    lower_bound = []
    upper_bound = []
    bounds_set = False;
    insertion_locations = []

    # some useful functions for playing with permutations
    @staticmethod
    def monotone_increasing(n):
        """Returns a monotone increasing permutation of length n.

        >>> Permutation.monotone_increasing(5)
        1 2 3 4 5
        """
        return Permutation(range(n))

    @staticmethod
    def monotone_decreasing(n):
        """Returns a monotone decreasing permutation of length n.

        >>> Permutation.monotone_decreasing(5)
        5 4 3 2 1
        """
        return Permutation(range(n)[::-1])

    @staticmethod
    def random(n):
        """Outputs a random permutation of length n.

        >>> len( Permutation.random(10) ) == 10
        True
        """
        L = list(range(n))
        random.shuffle(L)
        return Permutation(L)

    @staticmethod
    def random_avoider(n, B, simple=False, involution=False, verbose=-1):
        """Generates a (uniformly) random permutation which avoids the patterns
        contained in `B`.

        Parameters
        ----------
        B : PermSet or list of objects which can be coerced to Permutations
            Basis of permutations to be avoided
        simple : Boolean
            Restrict to simple permutations
        involution : Boolean
            Restrict to involutions
        verbose : int
            Level of verbosity (-1 for none). Doubling the integer doubles the
            number of messages printed

        Returns
        -------
        p : Permutation instance
            A permutation avoiding all the patterns in `B`

        >>> p = Permutation.random_avoider(8, [123])
        >>> p.involves(123)
        False
        """

        i = 1
        p = Permutation.random(n)
        while (involution and not p.is_involution()) \
            or (simple and not p.is_simple()) or not p.avoids_set(B):
            i += 1
            p = Permutation.random(n)
            if verbose != -1 and i % verbose == 0:
                print("Tested: "+str(i)+" permutations.");
        return p


    @staticmethod
    def listall(n):
        """Returns a list of all permutations of length `n`"""
        if n == 0:
            return []
        else:
            L = []
            for k in range(math.factorial(n)):
                L.append(Permutation(k,n))
            return L

    @staticmethod
    def standardize(L):
        """Standardizes a list `L` of unique elements by mapping them to the set
        0,1, ..., len(L) by an order-preserving bijection"""
        assert len(set(L)) == len(L), 'make sure elements are distinct!'
        ordered = L[:]
        ordered.sort()
        return [ordered.index(x) for x in L]

    @staticmethod
    def change_repr(representation=None):
        """Toggles (globally) between cycle notation or one-line notation. Note
        that internal representation is still one-line."""
        L = ['oneline', 'cycles', 'both']
        if representation in L:
            Permutation._REPR = representation
        else:
            k = input('1 for oneline, 2 for cycles, 3 for both\n ')
            k -= 1
            Permutation._REPR = L[k]

    @staticmethod
    def ind2perm(k, n):
        """De-indexes a permutation by a bijection from the set S_n to [n!].
        See also the `Permutation.perm2ind` method.

        Parameters
        ----------
        k : int
            An integer between 0 and n! - 1, to be mapped to S_n.
        n : int
            Length of the permutation.

        Returns
        -------
        p : Permutation instance

        """

        result = list(range(n))
        def swap(i,j):
            t = result[i]
            result[i] = result[j]
            result[j] = t
        for i in range(n, 0, -1):
            j = k % i
            swap(i-1,j)
            k //= i
        p = Permutation(result)
        return p

    #================================================================#
    # overloaded built in functions:

    def __new__(cls, p, n = None):
        """Creates a new permutation object. Supports a variety of creation
        methods.

        Parameters
        ----------
        p : Permutation, tuple, list, or int
        n : int (optional)
            If `p` is an iterable containing distinct elements, they will be
            standardized to produce a permutation of length `len(p)`.
            If `n` is given, and `p` is an integer, use `ind2perm` to create a
            permutation.
            If `p` is an integer with fewer than 10 digits, try to create a
            permutation from the digits.

        Returns
        -------
        Permutation instance

        """
        def _is_iterable(obj):
            """Quick utility to check if object is iterable."""
            res = True
            try: iter(obj)
            except: res = False
            return res
        entries = []
        if n:
            return Permutation.ind2perm(p, n)
        else:
            if isinstance(p, Permutation):
                return tuple.__new__(cls, p)
            elif _is_iterable(p):
                entries = list(p)[:]
            elif isinstance(p, int):
                entries = [int(digit) for digit in str(p)]

            if len(entries) == 0:
                if len(p) > 0:
                    err = 'Invalid inputs'
                    raise ValueError(err)

            standardization = Permutation.standardize(entries)
            return tuple.__new__(cls, standardization)

    # Not sure what this function does... Jay?
    def __init__(self,p,n=None):
        self.insertion_locations = [1]*(len(self)+1)

    def __call__(self,i):
        """Allows permutations to be called as functions. Used extensively for
        internal methods (e.g., counting cycles)."""
        return self[i]

    def oneline(self):
        """Returns the one-line notation representation of the permutation (as a
        sequence of integers 1 through n)."""
        s = ' '.join( str(entry + 1) for entry in self )
        return s

    def cycles(self):
        """Returns the cycle notation representation of the permutation."""
        stringlist = ['( ' + ' '.join([str(x + 1) for x in cyc]) + ' )'
                            for cyc in self.cycle_decomp()]
        return ' '.join(stringlist)

    def __repr__(self):
        """Tells python how to display a permutation object."""
        if Permutation._REPR == 'oneline':
            return self.oneline()
        if Permutation._REPR == 'cycles':
            return self.cycles()
        else:
            return '\n'.join([self.oneline(), self.cycles()])

    # __hash__, __eq__, __ne__ inherited from tuple class

    # def __hash__(self):
    #       '''allows fast comparisons of permutations, and allows sets of
    #       permutations'''
    #       return (self.perm2ind(), self.__len__()).__hash__()

    # def __eq__(self,other):
    #       ''' checks if two permutations are equal '''
    #       if len(self) != len(other):
    #           return False
    #       for i in range(len(self)):
    #           if self[i] != other[i]:
    #               return False
    #       return True

    # def __ne__(self,other):
    #       return not self == other

    def __mul__(self,other):
        """Returns the composition of two permutations."""
        assert len(self) == len(other)
        L = list(other)
        for i in range(len(L)):
            L[i] = self.__call__(L[i])
        return Permutation(L)

    def __pow__(self, power):
        """Returns the permutation raised to a (positive integer) power."""
        try:
            assert isinstance(power, int) and power >= 0
        except:
            err = 'Power must be a positive integer'
            raise ValueError(err)
        if power == 0:
            return Permutation(range(len(self)))
        else:
            ans = self
            for i in range(power - 1):
                ans *= self
            return ans

    def perm2ind(self):
        """De-indexes a permutation, by mapping it to an integer between 0 and
        len(self)! - 1. See also `Permutation.ind2perm`."""
        q = list(self)
        n = self.__len__()
        def swap(i,j):
            t = q[i]
            q[i] = q[j]
            q[j] = t
        result = 0
        multiplier = 1
        for i in range(n-1,0,-1):
            result += q[i]*multiplier
            multiplier *= i+1
            swap(i, q.index(i))
        return result

    def delete(self, idx):
        """Returns the permutation which results from deleting the entry at
        position `idx` from `self`. Recall that indices are zero-indexed.

        >>> Permutation(35214).delete(2)
        2 4 1 3
        """
        p = list(self)
        del p[idx]
        return Permutation(p)

    def insert(self,idx,val):
        """Returns the permutation resulting from inserting an entry with value
        just below `val` into the position just before the entry at position
        `idx`. Both the values and index are zero-indexed.

        >>> Permutation(2413).insert(2, 1)
        3 5 2 1 4

        >>> p = Permutation.random(10)
        >>> p == p.insert(4, 7).delete(4)
        True
        """
        p = list(self)
        for k in range(len(p)):
            if p[k] >= val:
                p[k] += 1
        p = p[:idx] + [val] + p[idx:]
        return Permutation(p)

    def complement(self):
        """Returns the complement of the permutation. That is, the permutation
        obtained by subtracting each of the entries from `len(self)`."""
        n = self.__len__()
        L = [n-1-i for i in self]
        return Permutation(L)

    def reverse(self):
        """Returns the reverse of the permutation."""
        q = list(self)
        q.reverse()
        return Permutation(q)

    def inverse(self):
        """Returns the group-theoretic inverse of the permutation."""
        p = list(self)
        n = self.__len__()
        q = [0 for j in range(n)]
        for i in range(n):
            q[p[i]] = i
        return Permutation(q)

    def plot(self):
        ''' Draws a plot of the given Permutation. '''
        n = self.__len__()
        array = [[' ' for i in range(n)] for j in range(n)]
        for i in range(n):
            array[self[i]][i] = '*'
        array.reverse()
        s = '\n'.join( (''.join(l) for l in array))
        # return s
        print(s)

    def cycle_decomp(self):
        n = self.__len__()
        seen = set()
        cyclelist = []
        while len(seen) < n:
            a = max(set(range(n)) - seen)
            cyc = [a]
            b = self(a)
            seen.add(b)
            while b != a:
                cyc.append(b)
                b = self(b)
                seen.add(b)
            cyclelist.append(cyc)
        cyclelist.reverse()
        return cyclelist

    def num_disjoint_cycles(self):
        return len(self.cycle_decomp())

    def sum(self, Q):
        return Permutation(list(self)+[i+len(self) for i in Q])

    def skew_sum(self, Q):
        return Permutation([i+len(Q) for i in self]+list(Q))


# Permutation Statistics - somewhat self-explanatory

    def fixed_points(self):
        sum = 0
        for i in range(self.__len__()):
            if self(i) == i:
                sum += 1
        return sum


    def skew_decomposable(self):
        p = list(self)
        n = self.__len__()
        for i in range(1,n):
            if set(range(n-i,n)) == set(p[0:i]):
                return True
        return False

    def sum_decomposable(self):
        p = list(self)
        n = self.__len__()
        for i in range(1,n):
            if set(range(0,i)) == set(p[0:i]):
                return True
        return False


    def numcycles(self):
        num = 1
        n = self.__len__()
        list = range(n)
        k = 0
        while list:
            if k in list:
                del list[list.index(k)]
                k = self(k)
            else:
                k = list[0]
                num += 1
        return num

    def descents(self):
        p = list(self)
        n = self.__len__()
        numd = 0
        for i in range(1,n):
            if p[i-1] > p[i]:
                numd+=1
        return numd

    def ascents(self):
        return self.__len__()-1-self.descents()

    def bends(self):
                # Bends measures the number of times the permutation p
                # "changes direction".  Bends is also the number of
                # non-monotone consecutive triples in p.
                # The permutation p can be expressed as the concatenation of
                # bend(p)+1 monotone segments.
        return len([i for i in range(1, len(self)-1) if (self[i-1] > self[i] and self[i+1] > self[i]) or (self[i-1] < self[i] and self[i+1] < self[i])])

    def peaks(self):
        return len([i for i in range(1, len(self)-1) if self[i-1] < self[i] and self[i+1] < self[i]])

    def trivial(self):
        return 0

    def order(self):
        L = map(len, self.cycle_decomp())
        return reduce(lambda x,y: x*y / fractions.gcd(x,y), L)

    def ltrmin(self):
        """Returns the positions of the left-to-right minima.
        >>> Permutation(35412).ltrmin()
        [0, 3]
        """
        n = self.__len__()
        L = []
        for i in range(n):
            flag = True
            for j in range(i):
                if self[i] > self[j]:
                    flag = False
            if flag: L.append(i)
        return L

    def rtlmin(self):
        """Returns the positions of the left-to-right minima.
        >>> Permutation(315264).rtlmin()
        [5, 3, 1]
        """
        rev_perm = self.reverse()
        return [len(self) - val - 1 for val in rev_perm.ltrmin()]

    def ltrmax(self):
        return [len(self)-i-1 for i in Permutation(self[::-1]).rtlmax()][::-1]

    def rtlmax(self):
        return [len(self)-i-1 for i in self.complement().reverse().ltrmin()][::-1]

    def numltrmin(self):
        p = list(self)
        n = self.__len__()
        num = 1
        m = p[0]
        for i in range(1,n):
            if p[i] < m:
                num += 1
                m = p[i]
        return num

    def inversions(self):
        """Returns the number of inversions of the permutation, i.e., the
        number of pairs i,j such that i < j and self(i) > self(j).

        >>> Permutation(4132).inversions()
        4
        >>> Permutation.monotone_decreasing(6).inversions() == 5*6 / 2
        True
        >>> Permutation.monotone_increasing(7).inversions()
        0
        """

        p = list(self)
        n = self.__len__()
        inv = 0
        for i in range(n):
            for j in range(i+1,n):
                if p[i]>p[j]:
                    inv+=1
        return inv

    def noninversions(self):
        p = list(self)
        n = self.__len__()
        inv = 0
        for i in range(n):
            for j in range(i+1,n):
                if p[i]<p[j]:
                    inv+=1
        return inv

    def bonds(self):
        numbonds = 0
        p = list(self)
        for i in range(1,len(p)):
            if p[i] - p[i-1] == 1 or p[i] - p[i-1] == -1:
                numbonds+=1
        return numbonds

    def majorindex(self):
        sum = 0
        p = list(self)
        n = self.__len__()
        for i in range(0,n-1):
            if p[i] > p[i+1]:
                sum += i + 1
        return sum

    def fixedptsplusbonds(self):
        return self.fixed_points() + self.bonds()

    def longestrunA(self):
        p = list(self)
        n = self.__len__()
        maxi = 0
        length = 1
        for i in range(1,n):
            if p[i-1] < p[i]:
                length += 1
                if length > maxi: maxi = length
            else:
                length = 1
        return max(maxi,length)

    def longestrunD(self):
        return self.complement().longestrunA()

    def longestrun(self):
        return max(self.longestrunA(), self.longestrunD())

    def christiecycles(self):
        # builds a permutation induced by the black and gray edges separately, and
        # counts the number of cycles in their product. used for transpositions
        p = list(self)
        n = self.__len__()
        q = [0] + [p[i] + 1 for i in range(n)]
        grayperm = range(1,n+1) + [0]
        blackperm = [0 for i in range(n+1)]
        for i in range(n+1):
            ind = q.index(i)
            blackperm[i] = q[ind-1]
        newperm = []
        for i in range(n+1):
            k = blackperm[i]
            j = grayperm[k]
            newperm.append(j)
        return Permutation(newperm).numcycles()

    def othercycles(self):
        # builds a permutation induced by the black and gray edges separately, and
        # counts the number of cycles in their product
        p = list(self)
        n = self.__len__()
        q = [0] + [p[i] + 1 for i in range(n)]
        grayperm = [n] + range(n)
        blackperm = [0 for i in range(n+1)]
        for i in range(n+1):
            ind = q.index(i)
            blackperm[i] = q[ind-1]
        newperm = []
        for i in range(n+1):
            k = blackperm[i]
            j = grayperm[k]
            newperm.append(j)
        return Permutation(newperm).numcycles()

    def sumcycles(self):
        return self.othercycles() + self.christiecycles()

    def maxcycles(self):
        return max(self.othercycles() - 1,self.christiecycles())

    def is_involution(self):
        return self == self.inverse()

    def threepats(self):
        p = list(self)
        n = self.__len__()
        patnums = {'123' : 0, '132' : 0, '213' : 0,
                             '231' : 0, '312' : 0, '321' : 0}
        for i in range(n-2):
            for j in range(i+1,n-1):
                for k in range(j+1,n):
                    patnums[''.join(map(lambda x:
                                                            str(x+1),Permutation([p[i], p[j], p[k]])))] += 1
        return patnums

    def fourpats(self):
        p = list(self)
        n = self.__len__()
        patnums = {'1234' : 0, '1243' : 0, '1324' : 0,
                             '1342' : 0, '1423' : 0, '1432' : 0,
                             '2134' : 0, '2143' : 0, '2314' : 0,
                             '2341' : 0, '2413' : 0, '2431' : 0,
                             '3124' : 0, '3142' : 0, '3214' : 0,
                             '3241' : 0, '3412' : 0, '3421' : 0,
                             '4123' : 0, '4132' : 0, '4213' : 0,
                             '4231' : 0, '4312' : 0, '4321' : 0 }

        for i in range(n-3):
            for j in range(i+1,n-2):
                for k in range(j+1,n-1):
                    for m in range(k+1,n):
                        patnums[''.join(map(lambda x:
                                            str(x+1),list(Permutation([p[i], p[j], p[k], p[m]]))))] += 1
        return patnums

    def num_consecutive_3214(self):
        number = 0
        n = len(self)
        for i in range(n-3):
            if self[i+2] < self[i+1] < self[i] < self[i+3]:
                number += 1
        return number

    def coveredby(self):
        S = set()
        n = len(self)
        for i in range(n+1):
            for j in range(n+1):
                S.add(self.ins(i,j))
        return S

    def buildupset(self, height):
        n = len(self)
        L = [set() for i in range(n)]
        L.append( set([self]) )
        for i in range(n + 1, height):
            oldS = list(L[i-1])
            newS    = set()
            for perm in oldS:
                newS = newS.union(perm.coveredby())
            L.append(newS)
        return L

    def set_up_bounds(self):
        L = list(self)
        n = len(L)
        upper_bound = [-1]*n
        lower_bound = [-1]*n
        for i in range(0,n):
            min_above = -1
            max_below = -1
            for j in range(i+1,len(self)):
                if L[j] < L[i]:
                    if L[j] > max_below:
                        max_below = L[j]
                        lower_bound[i] = j
                else:
                    if L[j] < min_above or min_above == -1:
                        min_above = L[j]
                        upper_bound[i] = j
        return (lower_bound, upper_bound)

    def avoids(self, p, lr=0):
        #TODO Am I correct on the lr?
        """Check if the permutation avoids the pattern `p`.

        Parameters
        ----------
        p : Permutation-like object
        lr : int
            Require the last entry to be equal to this

        >>> Permutation(123456).avoids(231)
        True
        >>> Permutation(123456).avoids(123)
        False
        """
        if not isinstance(p, Permutation):
            p = Permutation(p)
        return not p.involved_in(self, last_require=lr)

    def avoids_set(self, B):
        """Check if the permutation avoids the set of patterns.

        Parameters
        ----------
        B : iterable of Permutation-like objects
            Can be a PermSet or an iterable of objects which can be coerced to
            permutations.

        >>> Permutation(123456).avoids_set([321, 213])
        True
        >>> Permutation(123456).avoids_set([321, 123])
        False
        """
        for p in B:
            if not isinstance(p, Permutation):
                p = Permutation(p)
            if p.involved_in(self):
                return False
        return True

    def involves(self, p, lr=0):
        """Check if the permutation avoids the pattern `p`.

        Parameters
        ----------
        p : Permutation-like object
        lr : int
            Require the last entry to be equal to this

        >>> Permutation(123456).involves(231)
        False
        >>> Permutation(123456).involves(123)
        True
        """

        if not isinstance(p, Permutation):
            p = Permutation(p)
        return p.involved_in(self,last_require=lr)

    def involved_in(self, P, last_require=0):
        """ Checks if the permutation is contained as a pattern in `P`.

        >>> Permutation(123).involved_in(31542)
        False
        >>> Permutation(213).involved_in(54213)
        True
        """
        if not isinstance(P, Permutation):
            P = Permutation(P)

        if not self.bounds_set:
            (self.lower_bound, self.upper_bound) = self.set_up_bounds()
            self.bounds_set = True
        L = list(self)
        n = len(L)
        p = len(P)
        if n <= 1 and n <= p:
            return True

        indices = [0]*n

        if last_require == 0:
            indices[len(self)-1] = p - 1
            while indices[len(self)-1] >= 0:
                if self.involvement_check(self.upper_bound, self.lower_bound, indices, P, len(self)-2):
                    return True
                indices[len(self)-1] -= 1
            return False
        else:
            for i in range(1, last_require+1):
                indices[n-i] = p-i
            if not self.involvement_check_final(self.upper_bound, self.lower_bound, indices, P, last_require):
                return False

            return self.involvement_check(self.upper_bound, self.lower_bound, indices, P, len(self) - last_require - 1)

    def involvement_check_final(self, upper_bound, lower_bound, indices, q, last_require):
        for i in range(1,last_require):
            if not self.involvement_fits(upper_bound, lower_bound, indices, q, len(self)-i-1):
                return False
        return True

    def involvement_check(self, upper_bound, lower_bound, indices, q, next):
        if next < 0:
            return True
        # print indices,next
        indices[next] = indices[next+1]-1

        while indices[next] >= 0:
            if self.involvement_fits(upper_bound, lower_bound, indices, q, next) and self.involvement_check(upper_bound, lower_bound, indices, q, next-1):
                return True
            indices[next] -= 1
        return False

    def involvement_fits(self, upper_bound, lower_bound, indices, q, next):
        return (lower_bound[next] == -1 or q[indices[next]] > q[indices[lower_bound[next]]]) and (upper_bound[next] == -1 or q[indices[next]] < q[indices[upper_bound[next]]])


    def occurrences(self, pattern):
        total = 0
        for subseq in itertools.combinations(self, len(pattern)):
            if Permutation(subseq) == pattern:
                total += 1
        return total



    def all_intervals(self, return_patterns=False):
        blocks = [[],[]]
        for i in range(2, len(self)):
            blocks.append([])
            for j in range (0,len(self)-i+1):
                if max(self[j:j+i]) - min(self[j:j+i]) == i-1:
                    blocks[i].append(j)
        if return_patterns:
            patterns = []
            for length in range(0, len(blocks)):
                for start_index in blocks[length]:
                    patterns.append(Permutation(self[start_index:start_index+length]))
            return patterns
        else:
            return blocks



    def all_monotone_intervals(self, with_ones=False):
        mi = []
        difference = 0
        c_start = 0
        c_length = 0
        for i in range(0,len(self)-1):
            if math.fabs(self[i] - self[i+1]) == 1 and (c_length == 0 or self[i] - self[i+1] == difference):
                if c_length == 0:
                    c_start = i
                c_length += 1
                difference = self[i] - self[i+1]
            else:
                if c_length != 0:
                    mi.append((c_start, c_start+c_length))
                c_start = 0
                c_length = 0
                difference = 0
        if c_length != 0:
            mi.append((c_start, c_start+c_length))

        if with_ones:
            in_int = []
            for (start,end) in mi:
                in_int.extend(range(start, end+1))
            for i in range(len(self)):
                if i not in in_int:
                    mi.append((i,i))
            mi.sort(key=lambda x : x[0])
        return mi

    def monotone_quotient(self):
        return Permutation([self[k[0]] for k in self.all_monotone_intervals(with_ones=True)])



    def maximal_interval(self):
        ''' finds the biggest interval, and returns (i,j) is one is found,
            where i is the size of the interval, and j is the index
            of the first entry in the interval

        returns (0,0) if no interval is found, i.e., if the permutation
            is simple'''
        for i in range(2, len(self))[::-1]:
            for j in range (0,len(self)-i+1):
                if max(self[j:j+i]) - min(self[j:j+i]) == i-1:
                    return (i,j)
        return (0,0)

    def simple_location(self):
        ''' searches for an interval, and returns (i,j) if one is found,
            where i is the size of the interval, and j is the
            first index of the interval

        returns (0,0) if no interval is found, i.e., if the permutation
            is simple'''
        mins = list(self)
        maxs = list(self)
        for i in range(1,len(self)-1):
            for j in reversed(range(i,len(self))):
                mins[j] = min(mins[j-1], self[j])
                maxs[j] = max(maxs[j-1], self[j])
                if maxs[j] - mins[j] == i:
                    return (i,j)
        return (0,0)

    def is_simple(self):
        ''' returns True is this permutation is simple, False otherwise'''
        (i,j) = self.simple_location()
        return i == 0

    def is_strongly_simple(self):
        return self.is_simple() and all([p.is_simple() for p in self.children()])

    def decomposition(self):
        base = Permutation(self)
        components = [Permutation([1])for i in range(0,len(base))]
        while not base.is_simple():
            assert len(base) == len(components)
            (i,j) = base.maximal_interval()
            assert i != 0
            interval = list(base[j:i+j])
            new_base = list(base[0:j])
            new_base.append(base[j])
            new_base.extend(base[i+j:len(base)])
            new_components = components[0:j]
            new_components.append(Permutation(interval))
            new_components.extend(components[i+j:len(base)])
            base = Permutation(new_base)
            components = new_components
        return (base, components)

    def inflate(self, components):
        assert len(self) == len(components), 'number of components must equal length of base'
        L = list(self)
        NL = list(self)
        current_entry = 0
        for entry in range(0, len(self)):
            index = L.index(entry)
            NL[index] = [components[index][i]+current_entry for i in range(0, len(components[index]))]
            current_entry += len(components[index])
        NL_flat = [a for sl in NL for a in sl]
        return Permutation(NL_flat)

    def right_extensions(self):
        L = []
        if len(self.insertion_locations) > 0:
            indices = self.insertion_locations
        else:
            indices = [1]*(len(self)+1)

        R = [j for j in range(len(indices)) if indices[j] == 1]
        for i in R:
            A = [self[j] + (1 if self[j] > i-1 else 0) for j in range(0,len(self))]
            A.append(i)
            L.append(Permutation(A))
        return L

    # def all_right_extensions(self, max_length, l, S):
    #       if l == max_length:
    #           return S
    #       else:
    #           re = self.right_extensions()
    #           for p in re:
    #               S.add(p)
    #               S = p.all_right_extensions(max_length, l+1, S)
    #       return S

    def all_extensions(self):
        S = set()
        for i in range(0, len(self)+1):
            for j in range(0, len(self)+1):
                # insert (i-0.5) after entry j (i.e., first when j=0)
                l = list(self[:])
                l.insert(j, i-0.5)
                S.add(Permutation(l))
        return permset.PermSet(S)

    def all_extensions_track_index(self, ti):
        L = []
        for i in range(0, len(self)+1):
            for j in range(0, len(self)+1):
                # insert (i-0.5) after entry j (i.e., first when j=0)
                l = list(self[:])
                l.insert(j, i-0.5)
                if j < ti:
                    L.append((Permutation(l), ti+1))
                else:
                    L.append((Permutation(l), ti))
        return L

    def show(self):
        if sys.platform == 'linux2':
            opencmd = 'gnome-open'
        else:
            opencmd = 'open'
        s = r"\documentclass{standalone}\n\usepackage{tikz}\n\n\\begin{document}\n\n"
        s += self.to_tikz()
        s += "\n\n\end{document}"
        dname = random.randint(1000,9999)
        os.system('mkdir t_'+str(dname))
        with open('t_'+str(dname)+'/t.tex', 'w') as f:
            f.write(s)
        subprocess.call(['pdflatex', '-output-directory=t_'+str(dname), 't_'+str(dname)+'/t.tex'],
            stderr = subprocess.PIPE, stdout = subprocess.PIPE)
        # os.system('pdflatex -output-directory=t_'+str(dname)+' t_'+str(dname)+'/t.tex')
        subprocess.call([opencmd, 't_'+str(dname)+'/t.pdf'],
            stderr = subprocess.PIPE, stdout = subprocess.PIPE)
        time.sleep(1)
        if sys.platform != 'linux2':
            subprocess.call(['rm', '-r', 't_'+str(dname)+'/'])

    def to_tikz(self):
        s = r'\begin{tikzpicture}[scale=.3,baseline=(current bounding box.center)]';
        s += '\n\t'
        s += r'\draw[ultra thick] (1,0) -- ('+str(len(self))+',0);'
        s += '\n\t'
        s += r'\draw[ultra thick] (0,1) -- (0,'+str(len(self))+');'
        s += '\n\t'
        s += r'\foreach \x in {1,...,'+str(len(self))+'} {'
        s += '\n\t\t'
        s += r'\draw[thick] (\x,.09)--(\x,-.5);'
        s += '\n\t\t'
        s += r'\draw[thick] (.09,\x)--(-.5,\x);'
        s += '\n\t'
        s += r'}'
        for (i,e) in enumerate(self):
            s += '\n\t'
            s += r'\draw[fill=black] ('+str(i+1)+','+str(e+1)+') circle (5pt);'
        s += '\n'
        s += r'\end{tikzpicture}'
        return s

    def shrink_by_one(self):
        return permset.PermSet([Permutation(p) for p in [self[:i]+self[i+1:] for i in range(0,len(self))]])

    def children(self):
        return self.shrink_by_one()

    def downset(self):
        return permset.PermSet([self]).downset()

    def sum_indecomposable_sequence(self):
        S = self.downset()
        return [len([p for p in S if len(p)==i and not p.sum_decomposable()]) for i in range(1,max([len(p) for p in S])+1)]

    def sum_indec_bdd_by(self, n):
        l = [1]
        S = list(self.children())
        while len(S) > 0 and len(S[0]) > 0:
            l = [len([s for s in S if not s.sum_decomposable()])]+l
            if l[0] > n:
                return False
            S = list(permset.PermSet(S).layer_down())
        return True

    def contains_locations(self, Q):
        locs = []
        sublocs = itertools.combinations(range(len(self)), len(Q))
        for subloc in sublocs:
            if Permutation([self[i] for i in subloc]) == Q:
                locs.append(subloc)

        return locs

    def rank_val(self, i):
        return len([j for j in range(i+1,len(self)) if self[j] < self[i]])

    def rank_encoding(self):
        return [self.rank_val(i) for i in range(len(self))]

    def num_rtlmax_ltrmin_layers(self):
        return len(self.rtlmax_ltrmin_decomposition())

    def rtlmax_ltrmin_decomposition(self):
        P = Permutation(self)
        num_layers = 0
        layers = []
        while len(P) > 0:
            num_layers += 1
            positions = sorted(list(set(P.rtlmax()+P.ltrmin())))
            layers.append(positions)
            P = Permutation([P[i] for i in range(len(P)) if i not in positions])
        return layers

    def num_inc_bonds(self):
        return len([i for i in range(len(self)-1) if self[i+1] == self[i]+1])

    def num_dec_bonds(self):
        return len([i for i in range(len(self)-1) if self[i+1] == self[i]-1])

    def num_bonds(self):
        return len([i for i in range(len(self)-1) if self[i+1] == self[i]+1 or self[i+1] == self[i]-1])

    def contract_inc_bonds(self):
        P = Permutation(self)
        while P.num_inc_bonds() > 0:
            for i in range(0,len(P)-1):
                if P[i+1] == P[i]+1:
                    P = Permutation(P[:i]+P[i+1:])
                    break
        return P

    def contract_dec_bonds(self):
        P = Permutation(self)
        while P.num_dec_bonds() > 0:
            for i in range(0,len(P)-1):
                if P[i+1] == P[i]-1:
                    P = Permutation(P[:i]+P[i+1:])
                    break
        return P

    def contract_bonds(self):
        P = Permutation(self)
        while P.num_bonds() > 0:
            for i in range(0,len(P)-1):
                if P[i+1] == P[i]+1 or P[i+1] == P[i]-1:
                    P = Permutation(P[:i]+P[i+1:])
                    break
        return P

    def all_syms(self):
        S = permset.PermSet([self])
        S = S.union(permset.PermSet([P.reverse() for P in S]))
        S = S.union(permset.PermSet([P.complement() for P in S]))
        S = S.union(permset.PermSet([P.inverse() for P in S]))
        return S

    def is_representative(self):
        return self == sorted(self.all_syms())[0]

    def greedy_sum(p):
        parts = []
        sofar = 0
        while sofar < len(p):
            if len(p)-sofar == 1:
                parts.append(Permutation(1))
                return parts
            i = 1
            while sofar+i <= len(p) and list(p[sofar:sofar+i]) == range(sofar,sofar+i):
                i += 1
            i -= 1
            if i > 0:
                parts.append(Permutation(range(i)))
            sofar += i
            i = 2
            while sofar+i <= len(p) and not (max(p[sofar:sofar+i]) - min(p[sofar:sofar+i])+1 == i and min(p[sofar:sofar+i]) == sofar):
                i += 1
            if sofar+i <= len(p):
                parts.append(Permutation(p[sofar:sofar+i]))
            sofar += i
        return parts

    def chom_sum(p):
        L = []
        p = p.greedy_sum()
        for i in p:
            if i.inversions() == 0:
                L.extend([Permutation(1)]*len(i))
            else:
                L.append(i)
        return L

    def chom_skew(p):
        return [r.reverse() for r in p.reverse().chom_sum()]

if __name__ == '__main__':
    import doctest
    doctest.testmod()


