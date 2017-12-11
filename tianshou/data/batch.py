import numpy as np
import gc


# TODO: Refactor with tf.train.slice_input_producer, tf.train.Coordinator, tf.train.QueueRunner
class Batch(object):
    """
    class for batch datasets. Collect multiple observations (actions, rewards, etc.) on-policy.
    """

    def __init__(self, env, pi, advantage_estimation_function): # how to name the function?
        self._env = env
        self._pi = pi
        self._advantage_estimation_function = advantage_estimation_function
        self._is_first_collect = True


    def collect(self, num_timesteps=0, num_episodes=0, apply_function=True): # specify how many data to collect here, or fix it in __init__()
        assert sum([num_timesteps > 0, num_episodes > 0]) == 1, "One and only one collection number specification permitted!"

        if num_timesteps > 0: # YouQiaoben: finish this implementation, the following code are just from openai/baselines
            t = 0
            ac = self.env.action_space.sample() # not used, just so we have the datatype
            new = True # marks if we're on first timestep of an episode
            if self.is_first_collect:
                ob = self.env.reset()
                self.is_first_collect = False
            else:
                ob = self.raw_data['observations'][0] # last observation!

            # Initialize history arrays
            observations = np.array([ob for _ in range(num_timesteps)])
            rewards = np.zeros(num_timesteps, 'float32')
            episode_start_flags = np.zeros(num_timesteps, 'int32')
            actions = np.array([ac for _ in range(num_timesteps)])

            for t in range(num_timesteps):
                pass

            while True:
                prevac = ac
                ac, vpred = pi.act(stochastic, ob)
                # Slight weirdness here because we need value function at time T
                # before returning segment [0, T-1] so we get the correct
                # terminal value
                i = t % horizon
                observations[i] = ob
                vpreds[i] = vpred
                episode_start_flags[i] = new
                actions[i] = ac
                prevacs[i] = prevac

                ob, rew, new, _ = env.step(ac)
                rewards[i] = rew

                cur_ep_ret += rew
                cur_ep_len += 1
                if new:
                    ep_rets.append(cur_ep_ret)
                    ep_lens.append(cur_ep_len)
                    cur_ep_ret = 0
                    cur_ep_len = 0
                    ob = env.reset()
                t += 1

        if num_episodes > 0: # YouQiaoben: fix memory growth, both del and gc.collect() fail
            # initialize rawdata lists
            if not self._is_first_collect:
                del self.observations
                del self.actions
                del self.rewards
                del self.episode_start_flags

            observations = []
            actions = []
            rewards = []
            episode_start_flags = []

            t_count = 0

            for _ in range(num_episodes):
                ob = self._env.reset()
                observations.append(ob)
                episode_start_flags.append(True)

                while True:
                    ac = self._pi.act(ob)
                    actions.append(ac)

                    ob, reward, done, _ = self._env.step(ac)
                    rewards.append(reward)

                    t_count += 1
                    if t_count >= 200: # force episode stop, just to test if memory still grows
                        break

                    if done: # end of episode, discard s_T
                        break
                    else:
                        observations.append(ob)
                        episode_start_flags.append(False)

            self.observations = np.array(observations)
            self.actions = np.array(actions)
            self.rewards = np.array(rewards)
            self.episode_start_flags = np.array(episode_start_flags)

            del observations
            del actions
            del rewards
            del episode_start_flags

            self.raw_data = {'observations': self.observations, 'actions': self.actions, 'rewards': self.rewards, 'episode_start_flags': self.episode_start_flags}
        
            self._is_first_collect = False

        if apply_function:
            self.apply_advantage_estimation_function()

        gc.collect()

    def apply_advantage_estimation_function(self):
        self.data = self._advantage_estimation_function(self.raw_data)

    def next_batch(self, batch_size): # YouQiaoben: referencing other iterate over batches
        rand_idx = np.random.choice(self.data['observations'].shape[0], batch_size)
        return {key: value[rand_idx] for key, value in self.data.items()}
