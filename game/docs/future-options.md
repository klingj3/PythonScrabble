
### II: General Difficulty Adaptivity
At this level, we will run an extensive count of all words appearing in both wikipedia and the scrabble dictionary
(as wikipedia text is so easily available and provides a pretty good use of advanced levels of speech) and through
this generate counts of the frequencies of all scrabble words. Through this, we can label how archaic certain
words are. This method is not perfect, as there are archaic words such as XI and QAT which are Scrabble mainstays,
so we will marry this data with an online database showing about 3000 scrabble games as complete by expert level
players. While the words here will of course also be archaic, we the mainstays within these games will provide
some insight as to which archaic words are more common.

Once we have this loose understanding of the difficulty associated with each word, players will be able to either
directly select a difficulty option on a scale from 1 to 10, or put in their Reddit usernames which can act as
a blueprint of this player's vocabulary to provide insight as to which level would be best for the player.

In addition, this stage will also add definitions to appear when an opponent plays a turn, so players can build their game and vocabulary.

### III: Advanced Strategy and Word Placement
This is where the AI will begin to get into the territory of machine learning, and this will be divided into two
sections. The first is related to words placement. As we all know, new scrabble players can oftentimes easily
place their tiles in a way that sets up their opponents for really good or easy moves by open vowel placement or
having building space next to score multipliers. In order for this AI to both be competitive and accurately
approximate human performance, this is an important strategic consideration. Their are two main approaches which
could be taken:

#### 1. Linear Regression tuned through Genetic Algorithms
While GA doesn't really have that much use in this day and age, I think in this scenario it might prove as a good
method for tuning the various parameters for linear regression in approximation the risk value in a particular move.
Typical regression training techniques are predicated on relatively immediate understanding of the accuracy of an
action, whereas in this game strategic considerations may not be made apparent until the end of the game. While GA
is slower than more typical training methods, it should be able to approximate correct strategic considerations.

#### 2. Reinforcement Learning
As is common for the training of game agents, we could also apply reinforcement learning for this section.
However the most obvious issue with this approach are the virtually infinite (there are many orders of magnitude
more theoretical games of scrabble than there are atoms in the universe) possible state spaces. However, we could
collapse this state space into just considering the tiles which are now accessible for adding words onto as
well as the multipliers on these now usable tiles. This state space may still be too large to be useful, but
considering the much faster training of a reinforcement learning agent than a genetic algorithm, it is an
approach worth considering. 

### IV: Word Faking
One of the skills in Scrabble is the ability to play a fake word with confidence. This part actually wouldn't be 
that difficult to complete, as you could use either a LSTM (which is overkill, but hey it'll work) in order to
create fake words which approximate the patterns of real words, much in the same way I've seen LSTMs used in 
natural language generation and character-wise predictions as to the origins of a word. The broader difficulty 
with this feature will be to determine when the Agent will attempt to play one of these words, and what difficulty
levels will correspond to what level of word-faking. 