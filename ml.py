import os
import gym

environment_name = 'CartPole-v0'
env = gym.make(environment_name)

episodes = 5

for episode in range(1, episodes + 1):
    state = env.reset()
    done = False
    score = 0

    while not done:
        env.render()
        action = env.action_space.sample()
        n_state, reward, done, info = env.step(action)
        score += reward

    print(f"{episode : }, {score :}")

env.close()
