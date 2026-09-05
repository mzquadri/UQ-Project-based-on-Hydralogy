# Uncertainty Quantification in Hydrology

Project seminar, Mathematical Methods for Uncertainty Quantification in Hydrology.
Chair of Hydrology and River Basin Management, Technical University of Munich,
winter semester 2025/26. Group B.

A hydrological model that fits an observed flood event well is not the same thing
as a model you can trust. This repository is the record of a seminar that took one
calibrated rainfall-runoff model and asked, in five steps, how much of its apparent
skill survives contact with the uncertainty around it: in the parameters, in the
rainfall that drives it, and in the discharge it is scored against.

The short answer, and the result the whole sequence builds to, is that the
observations are the weak point. Adding realistic noise to the rainfall leaves the
fit essentially untouched. Propagating realistic rating-curve error into the
observed discharge costs about 0.15 of Nash-Sutcliffe efficiency, and recalibrating
the model against the corrupted record wins back almost none of it.

## Authorship

This is a three-person group submission, and the work is joint. What the git
history records about who committed what:

| Author | Contribution as recorded in the history |
|:--|:--|
| Christine Leers | First working versions of the calibration, local and global sensitivity, and both uncertainty assignment scripts, plus the running task list the group worked from |
| Yihan Shen | Exercise 1 |
| Mohd Zamin Quadri | HBV and Cython integration and data configuration, the production runs behind `results/`, consolidation of the group material into this repository, and report assembly |

Commit counts are a poor measure of who did what here. Most of Christine's commits
add a single file; the consolidation commits move several hundred at once. Neither
number reflects effort. Treat the scientific work as the group's.

## The model and the event

| Property | Value |
|:--|:--|
| Model | HBV001a, a lumped conceptual rainfall-runoff model by Faizan Anwar |
| Parameters | 18, across snow, soil moisture, upper and lower reservoir modules |
| Time step | Hourly |
| Forcing | Temperature, precipitation, potential evapotranspiration |
| Event | A single short, rainfall-dominated high-flow event |
| Objective | 1 minus Nash-Sutcliffe efficiency, minimised |

The event is short and rainfall-dominated, which matters for reading everything
below: it is why the groundwater store turns out to be irrelevant here, and it is
not a general statement about the model.

## Assignment 1: calibration, and what the fit rests on

![Calibration and process turn-off](docs/figures/01_calibration.png)

Differential evolution (`scipy.optimize.differential_evolution`, strategy
`best1bin`, population size 10) over the 18 parameters, run for 419 generations and
75,480 model evaluations. The best objective reached is 0.0924, an NSE of **0.9076**.
The search is within 0.001 of its final value by generation 308.

Individual process stores were then switched off and the model re-run with the
calibrated parameters:

| Configuration | NSE | Reading |
|:--|:--:|:--|
| All processes on | 0.9076 | The calibrated baseline |
| Groundwater off | 0.9076 | No measurable effect on this event |
| Upper reservoir off | 0.9076 | No measurable effect on this event |
| Snow off | 0.4959 | Snowmelt supplies a large part of the volume |
| Lower reservoir off | -0.7539 | The model collapses |

An NSE below zero means the model predicts the event worse than simply using the
mean of the observations would. The lower reservoir is not a refinement here, it is
load-bearing.

## Assignment 2: local sensitivity around the optimum

Each parameter was perturbed one at a time from -30% to +30% in 120 steps, holding
the others at their calibrated values, and scored by the maximum absolute relative
change in the objective. Near the optimum the ranking is led by `sl0_fcy` (field
capacity), followed by `sl0_dth`, `lrr_dre`, the snowmelt factors `snw_pmf` and
`snw_amf`, and `urr_ulc`.

Roughly ten of the eighteen parameters are effectively inactive in this
neighbourhood, for four distinguishable reasons: the perturbation is clamped at a
bound, the process is inactive for this event, the response surface is flat, or the
calibrated value is small enough that a 30% change is negligible. Files recording
which perturbations fell outside the parameter bounds are kept in
`results/assignment2/`, because a parameter that appears insensitive only because
its range was clipped is a different finding from one that is genuinely flat.

## Assignment 3: global sensitivity, and a configuration that fails

![Sobol total-order indices under four configurations](docs/figures/02_global_sensitivity.png)

Sobol variance decomposition with Saltelli sampling via `SALib`, run under two
sampling ranges crossed with two objectives.

| Configuration | V(Y) | Leading parameter | Sum of ST |
|:--|:--:|:--|:--:|
| Full range, NSE | 0.463 | `lrr_dre` (0.59) | 1.856 |
| Narrow range, NSE | 0.00194 | `sl0_fcy` (0.50) | 1.345 |
| Narrow range, logNSE | 0.109 | `lrr_dre` (0.55) | 1.135 |
| Full range, logNSE | 0.000032 | not usable | 3.072 |

Three things are worth drawing out.

The ranking is not a property of the model alone. Across the full parameter range
the lower-reservoir parameters `lrr_dre` and `lrr_dth` dominate; restricted to a
narrow range around the optimum, `sl0_fcy` leads instead, agreeing with the local
analysis of Assignment 2. Both are correct answers to different questions.

Total-order indices sum well above one, to 1.856 in the full-range NSE case. That is
not an error. Total-order indices count interaction effects once for every parameter
involved, so the excess over one measures how far the parameters act jointly rather
than independently.

The fourth configuration is kept because it fails. First-order indices cannot sum to
more than one, and here they sum to 6.28, which says the estimator has broken down
rather than that the parameters are important. Taking the logarithm of a
near-zero flow diverges, and sampling logNSE over the full range guarantees
near-zero flows. It is reported rather than deleted.

Narrowing the sampling range shrinks the output variance by a factor of about **238**
under NSE, from 0.463 to 0.00194.

## Assignments 4 and 5: error in the input against error in the output

![Input against output uncertainty](docs/figures/03_input_vs_output_uncertainty.png)

Both studies generate 2,000 perturbed series, run the model with the Assignment 1
parameters, and then recalibrate against each perturbed series in turn.

**Assignment 4, precipitation.** Each precipitation value is multiplied by an
independent Gaussian factor C drawn from N(1.0, 0.083), clipped to [0.75, 1.25] so no
value moves by more than 25%. The realised mean absolute change in precipitation is
6.62%. Mean NSE with the reference parameters is **0.9073**, against a calibrated
baseline of 0.9077: a loss of 0.0004. Recalibration returns 0.0002 of that, and 834
of the 2,000 noisy series happen to score better than the unperturbed record.

That last number is the useful one. If roughly 40% of corrupted inputs produce a
better score than the true input, then differences of this size carry no information
about input quality.

**Assignment 5, discharge.** Observed water level is perturbed by an additive
uniform draw on [-25, +25] cm, and the perturbed level is converted back to
discharge through a fitted rating curve: two power laws blended by a sigmoid,
fitting the stage-discharge data with R squared **0.9987** against 0.8831 for a
single global power law. Mean NSE falls to **0.7592**. Not one of the 2,000 series
scores better than the baseline, and recalibration recovers 5.76% of the loss.

The asymmetry is the point of the seminar. The model can absorb noise in what drives
it. It cannot absorb error in what it is scored against, and no amount of refitting
will reveal that the target itself is wrong.

## Exercises

Three exercises sit alongside the five assignments. They use different models and
tools, and their material is archived rather than laid out in the tree.

**Exercise 1** is a notebook, `code/EX1/EX1_MMUQ_Group_B.ipynb`, committed by Yihan
Shen.

**Exercise 2** is a groundwater problem rather than a rainfall-runoff one: a
MODFLOW-2005 flood and river model driven by SPOTPY's parallel DREAM sampler,
`results/Ex 2 parallel DREAM-20260111.zip`. DREAM is an adaptive Markov chain Monte
Carlo method, so this is the Bayesian counterpart to the point-estimate calibration
of Assignment 1. It was run across four MPI ranks, and the archive holds the setup
(`spot_setup_modflow.py`, `run_dream.py`), the per-rank model directories, and
posterior parameter uncertainty plots for the Alzpitz, B1, B3 and B4 observation
points.

**Exercise 3** applies ROPE, robust parameter estimation by data depth, to daily HBV
runs for catchment 420 over two decades.

![Choosing the ROPE threshold](docs/figures/04_rope_threshold.png)

ROPE keeps the deepest parameter sets among those scoring below an objective
threshold. Lowering that threshold admits more sets, until the sets it admits stop
lying inside the region they themselves define. Sweeping the threshold down from 1.0
and stopping at the lowest value whose outside ratio is still under 1% selects
**0.6** for 1971 to 1980, keeping **405** parameter sets. The same procedure over 1981
to 1990 settles at **0.4** and keeps **280**. The decade the model is calibrated on
changes how tightly its parameters can be pinned down.

The Exercise 3 archive is 2.1 GB. The summary files that state these results total
17 KB, and `scripts/extract_exercise3_summaries.py` lifts them into
`results/exercise3_rope/` so the conclusions can be read, and the figure regenerated,
without downloading the archive.

## What is verified here, and what is not

These are versioned seminar results, not independently re-executed claims. Being
specific about the difference:

- Every number in this README is checked against the files in `results/` by
  `python scripts/check_claims.py`, which fails if the two disagree. Every figure is
  generated from those same files by `scripts/figures/generate_figures.py`, so a
  figure cannot show a value the runs did not produce.
- The full scientific reruns cannot be reproduced from this repository alone. The
  forcing and area inputs and the course-provided `hmg` package containing `HBV001A`
  are not included, and Assignments 1 to 4 need them.
- The Exercise 2 and Exercise 3 archives are a different case: each carries its own
  model inputs and supporting packages, and the Exercise 3 archive also contains a
  checked-in virtual environment and about 2 GB of intermediate simulation output.
  They are preserved as submitted rather than repackaged.
- Assignment 5 reports a "calculated NSE" of 0.9000 for the reference parameters
  against the rating-curve reconstruction of the unperturbed record, distinct from
  the 0.9077 measured against the original observations. The gap is the rating curve
  fit itself, before any perturbation is applied.

## Reproducing what can be reproduced

```bash
git lfs install
git clone https://github.com/mzquadri/UQ-Hydrology-Seminar-TUM.git
cd UQ-Hydrology-Seminar-TUM
python -m pip install -r requirements.txt
```

Some report paths are long. On Windows, clone to a short path with long paths
enabled:

```powershell
git clone --config core.longpaths=true https://github.com/mzquadri/UQ-Hydrology-Seminar-TUM.git C:\g\h
```

Checks and figures, none of which need the course data:

```bash
python scripts/check_repository.py             # artifacts present and code parses
python scripts/extract_exercise3_summaries.py  # ROPE summaries out of the archive
python scripts/check_claims.py                 # README numbers against results/
python scripts/figures/generate_figures.py     # regenerate docs/figures/
```

Re-running the assignments themselves additionally needs the course inputs and the
`hmg` package, located through environment variables rather than by editing source:

```powershell
$env:HYDROLOGY_DATA_DIR = "C:\path\to\authorized\hmg\data"
$env:HYDROLOGY_RATING_CURVE_PATH = "C:\path\to\time_series___24163005_without_Outliers.csv"
```

`HYDROLOGY_DATA_DIR` must contain `time_series___24163005.csv` and
`area___24163005.csv`. The rating-curve path is needed only by Assignment 5's
curve-fitting script.

## Layout

```
code/                    Assignment scripts, one per assignment
  EX1/                   Exercise 1 notebook
  EX3/                   Exercise 3 archive (Git LFS, 2.1 GB)
results/                 Run outputs, one directory per assignment
  exercise3_rope/        ROPE summaries extracted from the archive
  Ex 2 parallel DREAM-*  Exercise 2 archive (Git LFS, 372 MB)
docs/figures/            Figures, generated from results/
docs/diagrams/           Workflow overview
scripts/                 Checks and figure generation
Overleaf_Projects/       LaTeX report source and figures
```

Two archives are tracked with [Git LFS](https://git-lfs.github.com/):
`code/EX3/rope_exercise3_pycodes_Final.zip` at 2.1 GB and
`results/Ex 2 parallel DREAM-20260111.zip` at 372 MB. Cloning without Git LFS
installed leaves them as pointer files; everything else in the repository still
works, including the figures.

## References

The report bibliography is
`Overleaf_Projects/Mathematical methods for uncertainty quantification in hydrology/literature.bib`.
The works it cites:

| Reference | Topic |
|:--|:--|
| Storn and Price (1997) | Differential evolution |
| Saltelli et al. (2002) | Sobol sensitivity indices |
| Oudin et al. (2006) | Impact of biased and randomly corrupted inputs |
| Moriasi et al. (2007) | Model evaluation guidelines and NSE |
| Beven (2012) | Rainfall-Runoff Modelling: The Primer |
| Le Coz et al. (2014) | Bayesian estimation of rating curves |
| Smith (2014) | Uncertainty quantification, theory and implementation |
| Houska et al. (2015) | SPOTPY, the parameter optimisation package used in Exercise 2 |
| Westerberg et al. (2020) | Calibration with uncertain discharge data |

## Licence

Coursework, published to be read rather than reused, with three authors who would
all have to agree to any reuse. See [LICENSE](LICENSE), which also records what
belongs to the Chair rather than to us.
