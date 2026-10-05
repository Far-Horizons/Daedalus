# Daedalus documentation
## The goal of Daedalus
The end product this project is aimed at is a collection of tools and automations that take care of all my bug-bounty related needs. Whether or not it will ever reach that state is uncertain, but the project isn't even really about that end-goal. My main priority is learning: This is the single largest priority. This entire project is building tools that I could have just downloaded and easily wired together. I choose not to do this as I want to deepen my understanding of everything related to cybersec (currently with a BBH focus). I want to have a deeper understanding of how tools work under the hood, how various bug classes work, how they can be detected, how websites and scanning these website work, basically everything. This project is born out of this desire to learn, and a passion for understanding the deeper mechanisms of things.

## AI coding agent usage
As this is a project in which the highest priority is learning, I will not be "vibecoding" anything. I will most likely use AI to help grasp concepts that I don't understand yet, learn new things, get feedback on my code, and if I'm stuck, steer me in the right direction. I believe these are all use cases that help me learn, rather than take over the process itself (which would mean I learn very little or nothing at all).

## Modularity
The goal is to have Daedalus built so that every module is functional on it's own, while at the same time having smooth interaction with the other modules. For example, both Proteus (subdomain permutation engine) and Argus (subdomain monitoring) will run completely independently, but are also able to smoothly feed each-other data regarding subdomains.

## Documentation
Every module will contain its own README, which shortly explains what the module is about. There is also a `Daedalus_Docs/` directory. This is an obsidian (.md) based documentation for the project. I have opted to use obsidian here as I have found it to be a great tool for learning, tracking interactions, etc. This documentation is currently not included in the repo, as it is still in a messy personal state.