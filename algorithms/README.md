# Algorithms!!!

[toc]

## DP Explanation.

The DP (Dynamic Programming) Algorithm works as follows:

### Break into Phrases

First, as input, we receive a chord progression (in Roman Numeral Analysis format) in the form of "phrases," smaller chord progressions most likely ending in a cadence (without rhythmic information). Here's an example:

```text
D: I vi I6 IV I64 V I
D: I6 V64 I IV6 V I6 V
D: I IV6 I6 IV I64 V7 vi
D: I6 V43 I I6 ii65 V I
A: I IV64 I vi ii6 V7 I
b: iv6 i64 iv iio6 i64 V7 i
A: IV IV V I6 ii V65 I
D: IV6 I V65 I ii65 V7 I
```

Since the last chord of a phrase (which ends a cadence) is most likely held before continuing the next phrase, it does not need to follow the rules of voice leading to connect to the first chord of the subsequent phrase. Hence, we can naturally split apart this progression into phrases and deal with them separately.

### Chord Voicing Generation

Then, for each chord in a phrase, we can generate appropriate voicings given the spacing and doubling rules. These rules are the following:

- Spacing Rules: 
	- Adjacent **top voices** are all ≤ one octave apart.
	- The **Tenor** and **Bass** are < two octaves apart.
	- None of the voices overlap.
- Doubling rules:
	- In **6/4 chords** (2nd-inversion triads), *always* double the **fifth**
	- In RP (root-position) and 1st-inversion **triads**, allow doubling any chord member that is not the contextual leading tone (LT).
	- In RP **triads**, also try incomplete chord structures (omit 5): tripled root, and doubled root with doubled third, as long as LT is not being doubled.
	- It is not necessary to double a not member in **Seventh Chords**, we simply voice the chord using each of its members once.
	- In RP **Seventh Chords**, aslo try incomplete chord structures (omit 5). The seventh cannot be doubled as it is a tendency tone by the PSR rule, so try doubling the root and doubling the third, as long as LT is not being doubled.

The purpose of these rules is to ensure that problematic voicings are impossible. This way, we have a basic guarantee of the quality of the output. These rules are, to some extent, heuristics: we cannot double leading tones or tendency tones because they must *tend* towards another tone that will create an objectionable parallelism down the road. This also reduces the quantity of potential voicings which we have to run DP on, significantly reducing search time.

### Pairwise Inspection

Next, we observe that in four-part writing, many voice leading rules apply in vacuum between two chords. The only context required is a contextual key that determines how tendency tones should resolve. For example, the progression `D: V7 vi` has a contextual key of `D`, so the LT `C#` should resovle to the tonic `D`. Whereas for a secondary dominant (tonicization), `D: V43/V/vi V7/vi` has a contextual key that is the `V/vi` of `D`, which is `E`. Hence, in this progression, the LT `D#` should resolve to the tonic `E`.

Under this model, our goal is to quantize the quality of voice leading between each adjacent pair of chords, and then find an arrangement of voicings of the chords in the given phrase that maximize the voice leading quality.

A convenient way to quantize this uses the notion of **cost**. We assign a cost to each pair of voicings of adjacent chords. These costs represent penalty from violations of voice leading conventions. And by finding an optimal arrangement of voicingsthat minimizes the cost, we also maximize the quality. This cost is called `voiceLeadingCost`, and takes as input the voicings of two chords as well as their respective Roman Numeral Thoroughbass figures as context.

Furthermore, to encourage use of some chords over others, such as preferring complete chords to incomplete ones and preferring root doublings to fifth doublings, we can assign an inherent cost to each chord, hereon called `chordCost`, that returns the cost of using a chord. The more preferable the chord, the lower the cost.

### Dynamic Search

Now, we can begin searching. Let's first store the roman numerals of the phrase in a list called `romanNumerals`, and let's store all the generated voicings in a list of lists called `voicings`. The length of these two lists are both `phraseLength`. The voicings of chord `x` of the phrase are located in the list stored as `voicings[x]`. Note that there is a different number of possible voicings for each chord, so the lengths of lists `voicings[x]` differ.[^1]

Next, create an identical table called `DP` where we will store the data of our dynamic search. We first prime the first row of `DP`, corresponding to the first chord, with the chord costs of each chord. (The pseudocode is 1-indexed for convenience.)

>**repeat** with i from 1 to length_of(voicings[1])
>	set DP[1][i] = chordCost(voicings[1][i], romanNumerals[1])
>end **repeat**

Afterwards, for each voicing in the subsequent chords, we want to store the minimal cost, and which voicing of the chord from the previous row gave this cost. To achieve this, we can use an iterative approach.

- For a given voicing `x` of chord `n`, we compare it to each voicing `y` of chord `n-1`
	- we add the cheapest route so far to voicing `y`, which we determined earlier when we iterated the voicings of chord `n-1`, `previousCost`, 
	- and add to it the `voiceLeadingCost` of `(y -> x)` and the `chordCost` of voicing `x`.
	- Then we choose the cheapest outcome, the `bestCurrentCost`, and store it together with the voicing `y` that achieved this cost into `DP`.

Let's see it in action. To start, we set `bestCurrentCost` to infinity and update it when a better cost is found.

>**repeat** with n from 2 to phraseLength #(rest of the chords)
>	**repeat** with x from 1 to length_of(voicings[n]) #(with all voicings of chord n)
>		set bestCurrentCost
>	end **repeat**
>end **repeat**



### Optimization by Pruning

### Documentation of `chordCost`

### Documentation of `voiceLeadingCost`


## Chord and Voice Leading Cost rules.

ti->do is held universally unless the progression takes place in a secondary dominant, in which the ti->do is evaluated in the key of chord1's secondary dominant application.

fa->mi is not held universally, as it most often concerns the V7 and viiº (think the bassline of IV to V, that breaks fa->mi.) This fa->mi is treated as a specific case of the PSR rule of non-dominant sevenths. Of course, it has to be as a particular case applied to viiº (and viiø7). 

~~Furthermore, it doesn't hurt to add a fa->mi rule with a smaller weight~~ (though we're not doing that right now)

### Optimizations

Finally, regarding `Music21`, which tends to be a little slow as it prefers flexibility to speed, [this article](http://dmitri.mycpanel.princeton.edu/music21.pdf) offers some advice on speeding up Music21. Command+F the search term "speed" to find.

## Voice Leading Rules Reference

General:
- https://music.utk.edu/theorycomp/courses/murphy/documents/PartWritingRules.pdf
(Incomplete triads need to be in root position)

64 chords need doubled bass:
- https://music.utk.edu/theorycomp/courses/murphy/documents/64chords.pdf
- https://musictheory.pugetsound.edu/mt21c/SummaryOfDoublingRules.html

Seventh chords in inversion are *always* **Complete**:
- https://davidkulma.com/musictheory/seventhchords

Incomplete seventh chords are necessary:
- https://musictheory.pugetsound.edu/mt21c/VoiceLeadingSeventhChordsIntro.html

## Benchmarking

The benchmarks are done with respect to [this](https://autoharmony.herokuapp.com/view/3).

<!-- Footnotes -->
[^1]: They are not necessarily different, but they need not be the same either.
