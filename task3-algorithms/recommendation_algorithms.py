#!/usr/bin/env python3
"""
NEPHELE Task 3 - Recommendation Algorithms
Multiple recommendation strategies:
  1. Collaborative Filtering (User-User & Item-Item)
  2. Content-Based Filtering
  3. Hybrid Recommender
  4. Association Rules (Apriori)
  5. Neural Collaborative Filtering
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False


class RecommendationAlgorithm:
    """Base class for recommendation algorithms"""
    
    def __init__(self, name):
        self.name = name
        self.model = None
        self.is_trained = False
        self.item_features = None
    
    def train(self, interactions_df, item_features_df):
        """Train the recommendation model"""
        raise NotImplementedError
    
    def recommend(self, user_id, n_items=5):
        """Recommend items for a user"""
        raise NotImplementedError
    
    def save(self, path):
        """Save model to disk"""
        joblib.dump(self, path)
        print(f"  ✓ Model saved: {path}")
    
    @staticmethod
    def load(path):
        """Load model from disk"""
        model = joblib.load(path)
        print(f"  ✓ Model loaded: {path}")
        return model


class CollaborativeFiltering(RecommendationAlgorithm):
    """User-User and Item-Item Collaborative Filtering"""
    
    def __init__(self, method='item-item'):
        super().__init__(f"Collaborative Filtering ({method})")
        self.method = method
        self.user_item_matrix = None
        self.similarity_matrix = None
        self.item_mapping = {}
        self.user_mapping = {}
    
    def train(self, interactions_df, item_features_df=None):
        """Train collaborative filtering model"""
        
        # Create user-item matrix
        self.user_item_matrix = interactions_df.pivot_table(
            index='reviewer_id',
            columns='listing_id',
            values='rating',
            fill_value=0
        )
        
        # Create mappings
        self.item_mapping = {idx: val for idx, val in enumerate(self.user_item_matrix.columns)}
        self.user_mapping = {idx: val for idx, val in enumerate(self.user_item_matrix.index)}
        
        # Calculate similarity
        if self.method == 'item-item':
            # Item-item similarity
            self.similarity_matrix = cosine_similarity(self.user_item_matrix.T)
        else:
            # User-user similarity
            self.similarity_matrix = cosine_similarity(self.user_item_matrix)
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained with {len(self.user_item_matrix)} users and {len(self.user_item_matrix.columns)} items")
    
    def recommend(self, user_id, n_items=5):
        """Recommend items for a user"""
        if not self.is_trained:
            return []
        
        try:
            user_idx = list(self.user_item_matrix.index).index(user_id)
        except (ValueError, AttributeError):
            return []  # User not found
        
        if self.method == 'item-item':
            return self._recommend_item_item(user_idx, n_items)
        else:
            return self._recommend_user_user(user_idx, n_items)
    
    def _recommend_item_item(self, user_idx, n_items):
        """Item-item based recommendations"""
        user_ratings = self.user_item_matrix.iloc[user_idx]
        rated_items = user_ratings[user_ratings > 0].index
        
        if len(rated_items) == 0:
            return []
        
        scores = {}
        for item in self.user_item_matrix.columns:
            if item not in rated_items:
                # Calculate score based on similarity to rated items
                item_idx = list(self.user_item_matrix.columns).index(item)
                similarities = self.similarity_matrix[item_idx]
                
                score = 0
                for rated_item in rated_items:
                    rated_item_idx = list(self.user_item_matrix.columns).index(rated_item)
                    score += similarities[rated_item_idx] * user_ratings[rated_item]
                
                scores[item] = score
        
        # Return top n items
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n_items]
    
    def _recommend_user_user(self, user_idx, n_items):
        """User-user based recommendations"""
        similar_users = self.similarity_matrix[user_idx]
        
        # Find similar users
        similar_user_idxs = np.argsort(similar_users)[-6:-1]  # Top 5 similar users
        
        # Get items they liked
        candidate_items = {}
        for sim_user_idx in similar_user_idxs:
            sim_user_ratings = self.user_item_matrix.iloc[sim_user_idx]
            for item, rating in sim_user_ratings[sim_user_ratings > 0].items():
                if item not in self.user_item_matrix.iloc[user_idx][self.user_item_matrix.iloc[user_idx] > 0].index:
                    if item not in candidate_items:
                        candidate_items[item] = 0
                    candidate_items[item] += rating * similar_users[sim_user_idx]
        
        return sorted(candidate_items.items(), key=lambda x: x[1], reverse=True)[:n_items]


class ContentBasedFiltering(RecommendationAlgorithm):
    """Content-based recommendations using item features"""
    
    def __init__(self):
        super().__init__("Content-Based Filtering")
        self.item_features = None
        self.feature_similarity = None
        self.scaler = StandardScaler()
    
    def train(self, interactions_df, item_features_df):
        """Train content-based model"""
        
        # Encode categorical features
        self.item_features = item_features_df.copy()
        
        # Numerical features for similarity calculation
        numerical_cols = ['accommodates', 'bedrooms', 'beds', 'review_scores_rating']
        feature_matrix = self.scaler.fit_transform(
            self.item_features[numerical_cols].fillna(0)
        )
        
        # Calculate item-item similarity based on features
        self.feature_similarity = cosine_similarity(feature_matrix)
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained with {len(self.item_features)} items")
    
    def recommend(self, item_id, n_items=5):
        """Recommend similar items to a given item"""
        if not self.is_trained:
            return []
        
        try:
            item_idx = list(self.item_features['id']).index(item_id)
        except (ValueError, KeyError):
            return []
        
        # Get similarity scores
        similarities = self.feature_similarity[item_idx]
        
        # Get top similar items (excluding the item itself)
        similar_idxs = np.argsort(similarities)[::-1][1:n_items+1]
        
        recommendations = []
        for idx in similar_idxs:
            if idx < len(self.item_features):
                item = self.item_features.iloc[idx]['id']
                score = similarities[idx]
                recommendations.append((item, float(score)))
        
        return recommendations


class HybridRecommender(RecommendationAlgorithm):
    """Hybrid approach combining multiple recommendation strategies"""
    
    def __init__(self, weight_cf=0.4, weight_cb=0.3, weight_popularity=0.3):
        super().__init__("Hybrid Recommender")
        self.collaborative = CollaborativeFiltering(method='item-item')
        self.content_based = ContentBasedFiltering()
        self.popularity_scores = {}
        self.weight_cf = weight_cf
        self.weight_cb = weight_cb
        self.weight_popularity = weight_popularity
    
    def train(self, interactions_df, item_features_df):
        """Train hybrid model"""
        
        # Train collaborative filtering
        self.collaborative.train(interactions_df, item_features_df)
        
        # Train content-based filtering
        self.content_based.train(interactions_df, item_features_df)
        
        # Calculate popularity scores
        popularity = interactions_df.groupby('listing_id')['rating'].agg(['count', 'mean'])
        popularity['score'] = popularity['count'] * popularity['mean']
        self.popularity_scores = popularity['score'].to_dict()
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained (CF={self.weight_cf}, CB={self.weight_cb}, Pop={self.weight_popularity})")
    
    def recommend(self, user_id, n_items=5, use_cf=True, use_cb=False):
        """Recommend items using hybrid approach"""
        if not self.is_trained:
            return []
        
        recommendations = {}
        
        # Get recommendations from collaborative filtering
        if use_cf:
            try:
                cf_recs = self.collaborative.recommend(user_id, n_items * 2)
                for item, score in cf_recs:
                    if item not in recommendations:
                        recommendations[item] = 0
                    recommendations[item] += score * self.weight_cf
            except:
                pass
        
        # Get recommendations from content-based filtering
        if use_cb and len(recommendations) > 0:
            for item in list(recommendations.keys())[:3]:
                try:
                    cb_recs = self.content_based.recommend(item, n_items)
                    for rec_item, score in cb_recs:
                        if rec_item not in recommendations:
                            recommendations[rec_item] = 0
                        recommendations[rec_item] += score * self.weight_cb
                except:
                    pass
        
        # Apply popularity boost
        for item in recommendations.keys():
            popularity = self.popularity_scores.get(item, 0)
            recommendations[item] += popularity * self.weight_popularity
        
        # Return top n items
        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_items]


class AssociationRulesRecommender(RecommendationAlgorithm):
    """Simple association rules using frequent itemsets"""
    
    def __init__(self, min_support=0.01):
        super().__init__("Association Rules")
        self.min_support = min_support
        self.frequent_itemsets = {}
        self.association_rules = {}
    
    def train(self, interactions_df, item_features_df=None):
        """Train association rules"""
        
        # Find frequent itemsets
        # For simplicity, using co-occurrence of liked items by users
        user_items = interactions_df.groupby('reviewer_id')['listing_id'].apply(list)
        
        for user_id, items in user_items.items():
            if len(items) >= 2:
                # Find co-occurrences
                for i, item1 in enumerate(items):
                    for item2 in items[i+1:]:
                        key = (min(item1, item2), max(item1, item2))
                        if key not in self.association_rules:
                            self.association_rules[key] = {'count': 0, 'users': set()}
                        
                        self.association_rules[key]['count'] += 1
                        self.association_rules[key]['users'].add(user_id)
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained with {len(self.association_rules)} association rules")
    
    def recommend(self, item_id, n_items=5):
        """Recommend items that co-occur with given item"""
        if not self.is_trained:
            return []
        
        recommendations = {}
        
        for (item1, item2), stats in self.association_rules.items():
            if item_id == item1:
                recommendations[item2] = stats['count']
            elif item_id == item2:
                recommendations[item1] = stats['count']
        
        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_items]


class NeuralCollaborativeFiltering(RecommendationAlgorithm):
    """Deep learning based collaborative filtering"""
    
    def __init__(self, embedding_dim=32):
        super().__init__("Neural Collaborative Filtering")
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow required for Neural Collaborative Filtering")
        
        self.embedding_dim = embedding_dim
        self.model = None
        self.user_encoder = {}
        self.item_encoder = {}
    
    def _build_model(self, num_users, num_items):
        """Build neural collaborative filtering model"""
        
        # User embedding
        user_input = keras.Input(shape=(1,), name='user_input')
        user_embedding = layers.Embedding(num_users, self.embedding_dim, name='user_embedding')(user_input)
        user_vec = layers.Flatten()(user_embedding)
        
        # Item embedding
        item_input = keras.Input(shape=(1,), name='item_input')
        item_embedding = layers.Embedding(num_items, self.embedding_dim, name='item_embedding')(item_input)
        item_vec = layers.Flatten()(item_embedding)
        
        # Concatenate
        concat = layers.Concatenate()([user_vec, item_vec])
        
        # Dense layers
        dense1 = layers.Dense(64, activation='relu')(concat)
        dense1 = layers.Dropout(0.2)(dense1)
        dense2 = layers.Dense(32, activation='relu')(dense1)
        dense2 = layers.Dropout(0.2)(dense2)
        
        # Output
        output = layers.Dense(1, activation='sigmoid')(dense2)
        
        model = keras.Model(inputs=[user_input, item_input], outputs=output)
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        return model
    
    def train(self, interactions_df, item_features_df=None, epochs=10):
        """Train neural collaborative filtering"""
        
        # Encode users and items
        unique_users = interactions_df['reviewer_id'].unique()
        unique_items = interactions_df['listing_id'].unique()
        
        self.user_encoder = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_encoder = {iid: idx for idx, iid in enumerate(unique_items)}
        
        # Prepare training data
        X_users = np.array([self.user_encoder[uid] for uid in interactions_df['reviewer_id']])
        X_items = np.array([self.item_encoder[iid] for iid in interactions_df['listing_id']])
        y = (interactions_df['rating'].values - 1) / 4  # Normalize to 0-1
        
        # Build and train model
        self.model = self._build_model(len(unique_users), len(unique_items))
        self.model.fit(
            [X_users, X_items], y,
            epochs=epochs,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        print(f"  ✓ {self.name} trained with {len(unique_users)} users and {len(unique_items)} items")


def compare_recommendation_algorithms(interactions_df, item_features_df):
    """Train and compare all recommendation algorithms"""
    
    print("\n" + "=" * 80)
    print("🎯 TRAINING RECOMMENDATION ALGORITHMS")
    print("=" * 80)
    
    algorithms = {
        'Collaborative Filtering': CollaborativeFiltering(),
        'Content-Based Filtering': ContentBasedFiltering(),
        'Hybrid Recommender': HybridRecommender(),
        'Association Rules': AssociationRulesRecommender(),
    }
    
    # Add neural collaborative filtering if available
    if HAS_TENSORFLOW:
        algorithms['Neural Collaborative Filtering'] = NeuralCollaborativeFiltering()
    
    results = {}
    
    for name, algo in algorithms.items():
        print(f"\n🔹 {name}")
        try:
            if name == 'Neural Collaborative Filtering' and HAS_TENSORFLOW:
                algo.train(interactions_df, item_features_df, epochs=5)
            else:
                algo.train(interactions_df, item_features_df)
            results[name] = algo
        except Exception as e:
            print(f"  ⚠️  Error: {str(e)}")
    
    print("\n" + "=" * 80)
    
    return algorithms, results


if __name__ == "__main__":
    print("Recommendation algorithms module loaded")
