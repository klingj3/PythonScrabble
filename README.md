# PyScrabble

#### Requirements

The only nonstandard package used in this project is Colorama, which is used for coloring the board in human
v player games. To install, of course just type
`pip3 install colorama`

## Overview
I love scrabble, but I'm continuously disappointed by the quality of online scrabble games, both directly and in the
form of their opponents. A lot of them are slow, or require you to drag each tile on the board individually, or tell
you if a word you're trying to play is in the dictionary which defeats a key part of the game. 
This will be a command-line version (at least initially) which can be played much more quickly, and allow players to 
play invalid words  with all of the risk that contains. More than just providing 
an alternate vector through which to play scrabble, this will be an exercise in a unique brand of game AI, as well as
an algorithmic challenge as each possible move in scrabble has, including invalid options, a minimum of over a million
possible moves.

### Status 07/16
The level I (detailed below) agent is finished, as is all of the stylistic attributes for playing in the command line,
and all of the human commands can be interpreted correctly. To run ths game, simply traverse to the game file and run
game_manager.py, with two arguments for the number of human players and number of AI players. For example, to start
a game with just a human vs one AI opponent, type
`python3 game_manager.py 1 1`

[A game between two AI](https://i.imgur.com/Fwfxnv9.png)

## AI Development Plans
The crux of this little project, and AI opponent to play against in games of scrabble. Though it will start out
as the most barebones of opponents, the ultimate goal is to create a relatively dynamic opponent who will offer
any competitor a decent challenge and the opportunity to learn new words and scrabble techniques.

Here are the features to be implemented, at their various levels.

### I: Basic functionality - Completed!
At this level, the AI will have a complete scrabble dictionary loaded, and will play the best possible moves after
evaluating all legal moves and choosing the move with the best score, with no thoughts as to broader strategy. 
The human player will be able to play against this agent in the command line, with the following commands.

`quit` quits the game

`skip` skips a turn

`exchange LETTERS` exchanges the tiles in the string (here letters) at the expense of a turn.

`7 7 R PYTHON` plays the word in the direction `R` for right (or `D` for down), starting at x, y, coordinates `7, 7`

Alternatively, the user can just instruct games of AI vs AI to see the interesting words and moves they used.

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
