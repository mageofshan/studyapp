import torch
import torch.nn as nn
import torch.optim as optim

class FlashcardRLModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(FlashcardRLModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Example usage
# model = FlashcardRLModel(input_size=10, hidden_size=20, output_size=2)
# optimizer = optim.Adam(model.parameters(), lr=0.001)
# loss_fn = nn.CrossEntropyLoss()