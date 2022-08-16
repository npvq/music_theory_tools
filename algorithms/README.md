# Algorithms!!!

[toc]

The algorithms are contained in an SATB class object, who takes in keyword argument configuration parameters, which are referenced throughout this documentation.

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

Now, we can begin searching. Let's first store the roman numerals of the phrase in a list called `romanNumerals`, and let's store all the generated voicings in a list of lists called `voicings`. The length of these two lists are both `phraseLength`. The voicings of chord `x` of the phrase are located in the list stored as `voicings[x]`. Note that there is a different number of possible voicings for each chord, so the lengths of lists `voicings[x]` differ.[^f1]

Next, create an identical table called `DP` where we will store the data of our dynamic search. We first prime the first row of `DP`, corresponding to the first chord, with the chord costs of each chord. (The pseudocode is 1-indexed for convenience.)

```R
repeat with i from 1 to length_of(voicings[1])
	store DP[1][i] = chordCost(voicings[1][i], romanNumerals[1])
end repeat
```

Afterwards, for each voicing in the subsequent chords, we want to store the minimal cost, and which voicing of the chord from the previous row gave this cost. To achieve this, we can use an iterative approach.

- For a given voicing `x` of chord `n`, we compare it to each voicing `y` of chord `n-1`
	- we add the cheapest route so far to voicing `y`, which we determined earlier when we iterated the voicings of chord `n-1`, `previousCost`, 
	- and add to it the `voiceLeadingCost` of `(y -> x)` and the `chordCost` of voicing `x`.
	- Then we choose the cheapest outcome, the `bestCurrentCost`, and store it together with the voicing `y` that achieved this cost into `DP`.

Let's see it in action. To start, we set `bestCurrentCost` to infinity and update it when a better cost is found.

```python
repeat with n from 2 to phraseLength #(rest of the chords)
	repeat with x from 1 to length_of(voicings[n]) #(with all voicings of chord n)
		set bestCurrentCost = Infinity
		set bestCandidate = None
		repeat with y from 1 to length_of(voicings[n-1]) #(with all voicings of chord n-1)
			previousCost = DP[n-1][y].cost
			currentCost = previousCost + progressionCost(voicings[n-1][y], romanNumerals[n-1],
														 voicings[n][x], romanNumerals[n])
						  + chordCost(voicings[n][x], romanNumerals[n])

			if currentCost < bestCurrentCost then
				update bestCurrentCost = currentCost
				update bestCandidate = y # voicing that led to bestCurrentCost
			end if

		end repeat
		store DP[n][x] = (bestCurrentCost, bestCandidate)
	end repeat
end repeat
```

Of course, since the `chordCost` is invariable to `y`, we can add this after the loop. Many other similar implementation details have been left out in order to highlight the principle rationale of this algorithm.

Once we finish generating (memoizing) the `DP` table, we can *retrace* the solution.

- First, look at the last row (final chord) of `DP`, which is `DP[phraseLength]`. Iterate through to find the final chord whose solution has the lowest cost, let's call this `totalCost`.
- Let's say we find that the best solution (lowest cost) ends at index `z`, hence `totalCost = DP[phraseLength][z].cost`. 
	- Then, the voicing in chord `phraseLength-1` that led to this optimal solution is stored as `DP[phraseLength][z].candidate`.
	- We can repeat this procedure over and over to *retrace* the optimal solution, storing the candidates in a list as we go.
- Once we're done, we can reverse this list to get our solution.

Here is the pseudocode:

```python
set totalCost = Infinity
set z = None
repeat with i from 1 to length_of(DP[phraseLength])
	if DP[phraseLength][i].cost < totalCost then
		update totalCost = DP[phraseLength][i].cost
		update z = DP[phraseLength][i].candidate
	end if
end repeat

list solutionList
append voicing[phraseLength][z] to solutionList

repeat with n from phraseLength-1 down to 1
	update z = DP[n][z].candidate # best candidate voicing of previous chord
	append voicing[n][z] to solutionList
end repeat

reverse order of solutionList

return solutionList
```

### Analysis and Optimization by Pruning

This algorithm takes advantage of the modular nature of the fourpart voice-leading problem. Thanks to the four-voice limit (there are only four voices), the `chordCost` and `voiceLeadingCost` functions all run in constant time. The most complex part of the algorithm is when 

Hence, this algorithm runs in 𝒪(NL²) time, where N is `phraseLength` and L is the maximum number of voicings per chord, because its most complex part of the algorithm is checking every possible progression from the voicings of chord `n-1` to the voicings of chord `n`, taking at most c⋅L²+d operations (where c and d are constants). This is done at `N-1` times, giving us the analyzed running time of 𝒪(NL²).

This gives us yet another insight. Even though `chordCost` and `voiceLeadingCost` are constant-time operations, they are still rather slow because they utilize the `music21` library, and the sample input presented above could take up minutes to compute on a modern computer (as of 2022).

One way we can improve this algorithm is by, conterintuitively, taking away the guarantee of optimality. This algorithm guarantees that it will give us *one of* the best solutions in terms of cost, wherein most of the chords are voice led pretty well. However, by the third chord, some of the optimal subroutes would have exeeded ten times that of the final optimal `totalCost`! There is no need to keep computing the `voiceLeadingCosts` for those subroutes, as they won't be anywhere near optimal unless something goes terribly wrong. In this case, we are making a bet that it won't.

The bet is that by eliminating all subroutes that underperform the optimal subroute by a certain factor after each iteration, we will still end up with an optimal solution or something very close to that. This constant factor is called the `Confidence`. However, this leads to a problem, especially when the optimal subroute cost is either 0 or a very small value, as this can lead the elimination of too many routes, and resulting in a suboptimal solution. This is where the second constant, `Buffer` comes in. So now, after each iteration, we go through that row in `DP` and find the `minimalCost`. Then, we go through that row of `DP` once again and throw away every term whose `cost > Confidence * (minimalCost + Buffer)`. This can drastically reduce the computation cost, and in my experience testing common chord progressions, never led to a suboptimal solution (with higher cost).[^f2] With this, we have effectively pruned the search space without losing much performance.

Lastly, when two simple root position triads (like `I IV`) are presented as the first two chords, they both provide around eighty potential voicings, where a decent portion of the possible pairs result in good voice leading, we have no reason to stall the program and search through them for an "extra good" progression. This is when we can use `chordCost` to eliminate less preferable voicings of the first chord with the help of a constant that we will call `FirstBuffer`. Note that, at this point, `minimalCost` is likely but not necessarily 0. We want to eliminate more choices if both A and B are large (if the first two chords both have a lot of potential voicings). So the following formula was devised to eliminate voicings of the first chord:

`cost > Confidence * (minimalCost + FirstBuffer/(A*B))`

Through experimentation, it was found that a good value for FirstBuffer is 10,000.

#### Important Settings Values

| Config            | Type  | Usage                                                                                                                   | Default |
|-------------------|-------|-------------------------------------------------------------------------------------------------------------------------|---------|
| `dp_pruning`      | Bool  | Prune the search space during DP. Drastic speed improvements, but might   result in suboptimal solution.                | `True`  |
| `dp_prune_first`  | Bool  | If Pruning is on, determines whether to prune voicings of the first   chord.                                            | `True`  |
| `dp_confidence`   | Float | If Pruning is on, prunes all cost values greater than   `Confidence*(CurrentMin + Buffer)` after each iteration.        | `1.2`   |
| `dp_buffer`       | Int   | Buffer to make sure pruning is not overdone when CurrentBest is zero or   very small.                                   | `5`     |
| `dp_first_buffer` | Int   | If Prune_First is on, prunes all starting chord voicings greater than   `Confidence*(CurrentMin + First_Buffer/(A*B))`. | `10000` |

### Documentation of `chordCost`

Here are the rules and their respective costs for indivudual chords. The last chord is given special consideration for cadential purposes. Setting any cost value to zero effectively disables it.


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
[^f1]: They are not necessarily different, but they need not be the same either.
[^f2]: We also have to understand that "cost" is something we arbitrarily defined based off Common Practice Era voice leading rules and other conventions taught in music theory classes today. Hence, we cannot really say that a cost-optimal chord progression is necessarily better than one that is sligtly sub-optimal. And, at the end of the day, we just want a nicely voice-led chord progression without obvious objectionable parallel fifths, so it makes sense to prune the search space.
