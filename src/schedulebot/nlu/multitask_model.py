from transformers import AutoModel, PreTrainedModel, AutoConfig
import torch.nn as nn


class MultitaskModel(PreTrainedModel):
    """
    A custom Transformer model with two heads: one for intent classification
    and one for named entity recognition (token classification).
    """

    config_class = AutoConfig

    def __init__(self, config):
        super().__init__(config)

        # Load the base transformer model (e.g., DistilBERT)
        self.transformer = AutoModel.from_config(config)

        # --- Heads ---
        # 1. Intent Classification Head (MLP)
        self.intent_classifier = nn.Sequential(
            nn.Linear(config.dim, config.dim // 2),
            nn.GELU(),  # GELU is a smooth activation function, common in Transformers
            nn.Dropout(0.3),
            nn.Linear(config.dim // 2, self.config.num_intent_labels),
        )

        # 2. NER (Token Classification) Head (MLP)
        self.ner_classifier = nn.Sequential(
            nn.Linear(config.dim, config.dim // 2),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(config.dim // 2, self.config.num_ner_labels),
        )

        # Dropout layer for regularization
        self.dropout = nn.Dropout(config.seq_classif_dropout)

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        intent_label=None,  # For calculating intent loss
        labels=None,  # For calculating NER loss
    ):
        # Get the last hidden states from the base transformer model
        outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = (
            outputs.last_hidden_state
        )  # Shape: (batch_size, sequence_length, hidden_size)

        # --- Intent Logits ---
        # Use the [CLS] token's output for intent classification
        cls_token_output = sequence_output[:, 0, :]
        cls_token_output = self.dropout(cls_token_output)
        intent_logits = self.intent_classifier(cls_token_output)

        # --- NER Logits ---
        # Use all token outputs for NER
        sequence_output = self.dropout(sequence_output)
        ner_logits = self.ner_classifier(sequence_output)

        # --- Calculate Combined Loss ---
        total_loss = 0
        if intent_label is not None and labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            # Intent loss
            intent_loss = loss_fct(
                intent_logits.view(-1, self.config.num_intent_labels),
                intent_label.view(-1),
            )
            # NER loss (ignore padding tokens with label -100)
            ner_loss = loss_fct(
                ner_logits.view(-1, self.config.num_ner_labels), labels.view(-1)
            )
            # Combine the losses (you can also weight them if one task is more important)
            total_loss = intent_loss + ner_loss

        return {
            "loss": total_loss,
            "intent_logits": intent_logits,
            "ner_logits": ner_logits,
        }
