#!/bin/bash
# Runs the estimation scripts in order, rebuilds the tables of the online
# appendix, and runs the three checks.
#
#   ./run_all.sh              estimation from the person-level panels, then checks
#   ./run_all.sh --from-raw   first builds the panels from the survey files
#   ./run_all.sh --checks     checks only (needs no person-level file)
#
# The estimation steps need the person-level files described in README.md.
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
run() { (cd "$1" && shift && for s in "$@"; do echo ">>> $s"; $PY "$s.py"; done); }

if [ "$1" = "--from-raw" ]; then
  run income_dynamics/code 01_build_panel 02_sample_and_parents
  cp income_dynamics/data/intermediate/_panel_long_cache.pkl college_expansion/data/intermediate/
  run unified/code d0_dynamics_panel
  run income_dynamics/code 03_step0_residualize ws_panel_7wave m14_parent_process
fi

if [ "$1" != "--checks" ]; then
  # earnings process and measurement (Sections 3 and 4 of the paper)
  run income_dynamics/code 04_method1_md 05_method2_abgmm 06_mini_method3_randcoef m5_md_weighted_and_ridge \
      m7_md_cellweighted_boot m10_abgmm_table3 m13_mde_group_null m16_joint_moment_test m17_ab_diagnostics \
      m19_joint_process_by_group \
      m8_rank_attenuation_sim ws_methods_7wave ws_m3_strict_exogeneity_test ws_method1_arma11 ws_p1_6_ma1_rw \
      ws_05b_abb_stochastic_em
  run formal_results/code appendix_theory_computations
  # the premium, the expansion and the decomposition (Sections 5 to 7), the facts about the sample (Section 2), figures
  run college_expansion/code p16_census_pretrend
  run unified/code u8_premium_specifications u14_sample_facts u9_mature_age_earnings u12_returns_by_family_background \
      u13_decomposition_mature_age u16_identity_in_balanced_comparison u17_income_variance_by_wave
  # the Anderson-Rubin p-value of the return for all children at every point of the grid (first row of the table of returns)
  U9_BLOCKS=G run unified/code u9_mature_age_earnings
  U9_BLOCKS=R run unified/code u9_mature_age_earnings
  # the same three scripts with the rows weighted by the precision that the earnings process of Section 3 implies
  E_WEIGHTS=process run unified/code u9_mature_age_earnings u12_returns_by_family_background u13_decomposition_mature_age
  E_WEIGHTS=process U9_BLOCKS=G run unified/code u9_mature_age_earnings
  run unified/code u2_recovery_by_process u15_nonlinear_persistence_runs u3_online_appendix u4_premium_age_controls u7_error_structures
  # occupation by family background, the return without each province in turn, first-stage magnitudes, the gap among graduates
  run unified/code u18_occupation_by_family_background u19_province_and_identity_intervals u20_first_stage_magnitudes \
      u21_earnings_gap_by_degree u22_occupation_share_by_degree
  run unified/code fig_ridge fig_autocov fig_spec_curve
  # the figure of the paper shows thirteen of the fifteen specifications
  SPEC_PAPER=1 run unified/code fig_spec_curve
  run unified/code u10_growth_gap fig_first_stage build_paper_tables
  run online_appendix/build build_tables
fi

$PY unified/code/check_paper_numbers.py | tail -1
$PY online_appendix/build/check_part1_numbers.py | tail -1
$PY online_appendix/build/check_part2_numbers.py | tail -1
