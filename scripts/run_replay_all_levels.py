#!/usr/bin/env python3
"""Replay results of "run_evaluate_policy_all_levels.py" and compute reward.

Reads the files generated by "run_evaluate_policy_all_levels.py" and replays
the action logs to verify the result and to compute the total reward over all
runs.
"""

# IMPORTANT:  DO NOT MODIFY THIS FILE!
# Submissions will be evaluate on our side with our own version of this script.
# To make sure that your code is compatible with our evaluation script, make
# sure it runs with this one without any modifications.

import argparse
import os
import pickle
import subprocess
import sys
import typing

import numpy as np


class TestSample(typing.NamedTuple):
    difficulty: int
    iteration: int
    init_pose_json: str
    goal_pose_json: str
    logfile: str


def run_replay(sample: TestSample) -> float:
    """Run replay_action_log.py for the given sample.

    Args:
        sample (TestSample): Contains all required information to run the
            replay.

    Returns:
        The accumulated reward of the replay.
    """
    thisdir = os.path.dirname(__file__)
    replay_exe = os.path.join(thisdir, "replay_action_log.py")
    cmd = [
        replay_exe,
        "--difficulty",
        str(sample.difficulty),
        "--initial-pose",
        sample.init_pose_json,
        "--goal-pose",
        sample.goal_pose_json,
        "--logfile",
        sample.logfile,
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode != 0:
        stderr = res.stderr.decode("utf-8")
        raise RuntimeError(
            "Replay of {} failed.  Output: {}".format(sample.logfile, stderr)
        )

    # extract the reward from the output
    output = res.stdout.decode("utf-8").split("\n")
    label = "Accumulated Reward: "
    reward = None
    for line in output:
        if line.startswith(label):
            reward = float(line[len(label) :])
            break

    if reward is None:
        raise RuntimeError("Failed to parse reward from relay.")

    return reward


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_directory",
        type=str,
        help="Directory containing the generated log files.",
    )
    args = parser.parse_args()

    try:
        if not os.path.isdir(args.input_directory):
            print(
                "'{}' does not exist or is not a directory.".format(
                    args.input_directory
                )
            )
            sys.exit(1)

        levels = (1, 2, 3, 4)

        # load samples
        sample_file = os.path.join(args.input_directory, "test_data.p")
        with open(sample_file, "rb") as fh:
            test_data = pickle.load(fh)

        # run "replay_action_log.py" for each sample
        level_rewards = {level: [] for level in levels}
        for sample in test_data:
            print(
                "Replay level {} sample {}".format(
                    sample.difficulty, sample.iteration
                )
            )
            level_rewards[sample.difficulty].append(run_replay(sample))

        # report
        print("\n=======================================================\n")

        report = ""
        total_reward = 0
        for level, rewards in level_rewards.items():
            rewards = np.asarray(rewards)
            mean = rewards.mean()
            report += (
                "Level {} mean reward:\t{:.3f},\tstd: {:.3f}\n".format(
                    level, mean, rewards.std()
                )
            )
            total_reward += level * mean

        report += ("-------------------------------------------------------\n")
        report += ("Total Weighted Reward: {:.3f}\n".format(total_reward))

        print(report)

        # save report to file
        report_file = os.path.join(args.input_directory, "reward.txt")
        with open(report_file, "w") as fh:
            fh.write(report)

    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
