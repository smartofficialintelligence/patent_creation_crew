"""
Context Optimization Engine
Intelligent context truncation and compression for cost reduction
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from collections import Counter, defaultdict
import hashlib

# Set up logging
logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Context optimization strategies"""
    REMOVE_REDUNDANT = "remove_redundant"
    SUMMARIZE_BACKGROUND = "summarize_background"
    TRUNCATE_EXAMPLES = "truncate_examples"
    COMPRESS_REFERENCES = "compress_references"
    SEMANTIC_COMPRESSION = "semantic_compression"
    PRIORITY_FILTERING = "priority_filtering"

class ContentType(Enum):
    """Types of content for optimization"""
    TECHNICAL = "technical"
    LEGAL = "legal"
    BACKGROUND = "background"
    EXAMPLES = "examples"
    REFERENCES = "references"
    METADATA = "metadata"

@dataclass
class ContextSegment:
    """Segment of context for optimization"""
    content: str
    content_type: ContentType
    importance_score: float
    token_count: int
    is_essential: bool = False
    compression_ratio: float = 0.0
    
    @property
    def compressed_tokens(self) -> int:
        return int(self.token_count * (1 - self.compression_ratio))

@dataclass
class OptimizationResult:
    """Result of context optimization"""
    original_content: str
    optimized_content: str
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    strategies_applied: List[str]
    quality_preservation: float
    processing_time_ms: float
    
    @property
    def token_savings(self) -> int:
        return self.original_tokens - self.optimized_tokens
    
    @property
    def cost_savings_estimate(self) -> float:
        # Estimate cost savings (assuming $0.03 per 1K tokens)
        return self.token_savings * 0.00003

class ContextOptimizer:
    """Context optimization engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.optimization_history = []
        self.content_patterns = self._initialize_patterns()
        self.importance_weights = self._initialize_importance_weights()
        self.cached_optimizations = {}  # Cache for repeated content
        
        logger.info("🔧 Context Optimizer initialized")
        logger.info(f"   Strategies: {len(self.config['strategies'])}")
        logger.info(f"   Target compression: {self.config['target_compression']:.1%}")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'target_compression': 0.3,  # 30% compression target
            'quality_threshold': 0.9,   # Minimum quality preservation
            'max_tokens': 50000,        # Maximum context size
            'strategies': [
                OptimizationStrategy.REMOVE_REDUNDANT,
                OptimizationStrategy.SUMMARIZE_BACKGROUND,
                OptimizationStrategy.TRUNCATE_EXAMPLES,
                OptimizationStrategy.COMPRESS_REFERENCES,
                OptimizationStrategy.SEMANTIC_COMPRESSION
            ],
            'importance_weights': {
                'patent_claims': 1.0,
                'technical_details': 0.9,
                'legal_requirements': 0.9,
                'background_info': 0.6,
                'examples': 0.7,
                'references': 0.5,
                'metadata': 0.3
            },
            'compression_ratios': {
                'background': 0.5,
                'examples': 0.4,
                'references': 0.6,
                'metadata': 0.7
            },
            'essential_keywords': [
                'patent', 'claim', 'invention', 'method', 'system',
                'apparatus', 'process', 'technical', 'legal', 'requirement'
            ]
        }
    
    def _initialize_patterns(self) -> Dict[ContentType, List[str]]:
        """Initialize content identification patterns"""
        return {
            ContentType.TECHNICAL: [
                r'(?i)technical\s+(?:description|specification|details)',
                r'(?i)implementation\s+(?:details|specifics)',
                r'(?i)algorithm\s+(?:description|implementation)',
                r'(?i)system\s+(?:architecture|design)',
                r'(?i)method\s+(?:description|implementation)'
            ],
            ContentType.LEGAL: [
                r'(?i)legal\s+(?:requirements|compliance|analysis)',
                r'(?i)patent\s+(?:claims|application|filing)',
                r'(?i)intellectual\s+property',
                r'(?i)prior\s+art\s+(?:analysis|search)',
                r'(?i)claims?\s+(?:analysis|construction)'
            ],
            ContentType.BACKGROUND: [
                r'(?i)background\s+(?:information|context)',
                r'(?i)field\s+of\s+(?:invention|the\s+invention)',
                r'(?i)related\s+(?:work|art)',
                r'(?i)problem\s+(?:statement|description)',
                r'(?i)motivation\s+(?:for|of)'
            ],
            ContentType.EXAMPLES: [
                r'(?i)example\s+(?:\d+|implementation)',
                r'(?i)embodiment\s+(?:\d+|description)',
                r'(?i)use\s+case\s+(?:\d+|description)',
                r'(?i)illustration\s+(?:of|showing)',
                r'(?i)demonstration\s+(?:of|showing)'
            ],
            ContentType.REFERENCES: [
                r'(?i)reference\s+(?:cited|list)',
                r'(?i)bibliography',
                r'(?i)see\s+(?:also|reference)',
                r'(?i)patent\s+(?:publication|reference)',
                r'(?i)academic\s+(?:paper|publication)'
            ],
            ContentType.METADATA: [
                r'(?i)metadata\s+(?:information|details)',
                r'(?i)document\s+(?:properties|information)',
                r'(?i)file\s+(?:information|details)',
                r'(?i)creation\s+(?:date|time)',
                r'(?i)author\s+(?:information|details)'
            ]
        }
    
    def _initialize_importance_weights(self) -> Dict[str, float]:
        """Initialize importance weights for different content types"""
        return {
            'patent_claims': 1.0,
            'technical_details': 0.9,
            'legal_requirements': 0.9,
            'invention_description': 0.8,
            'implementation_details': 0.7,
            'background_info': 0.6,
            'examples': 0.7,
            'references': 0.5,
            'metadata': 0.3,
            'formatting': 0.2
        }
    
    def optimize_context(self, content: str, target_tokens: int = None, 
                        task_type: str = None, quality_requirement: float = 0.9) -> OptimizationResult:
        """Optimize context content"""
        
        start_time = datetime.now()
        
        # Check cache first
        content_hash = self._hash_content(content)
        if content_hash in self.cached_optimizations:
            cached_result = self.cached_optimizations[content_hash]
            logger.info(f"Using cached optimization (hash: {content_hash[:8]})")
            return cached_result
        
        # Analyze content
        segments = self._segment_content(content)
        original_tokens = self._count_tokens(content)
        
        # Determine target
        if target_tokens is None:
            target_tokens = min(original_tokens, self.config['max_tokens'])
        
        # Apply optimization strategies
        optimized_segments = self._apply_optimization_strategies(
            segments, target_tokens, task_type, quality_requirement
        )
        
        # Reconstruct content
        optimized_content = self._reconstruct_content(optimized_segments)
        optimized_tokens = self._count_tokens(optimized_content)
        
        # Calculate metrics
        compression_ratio = (original_tokens - optimized_tokens) / original_tokens if original_tokens > 0 else 0
        quality_preservation = self._estimate_quality_preservation(
            segments, optimized_segments, task_type
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create result
        result = OptimizationResult(
            original_content=content,
            optimized_content=optimized_content,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            compression_ratio=compression_ratio,
            strategies_applied=[s.value for s in self.config['strategies']],
            quality_preservation=quality_preservation,
            processing_time_ms=processing_time
        )
        
        # Cache result
        self.cached_optimizations[content_hash] = result
        
        # Store in history
        self.optimization_history.append(result)
        
        logger.info(f"Context optimized: {original_tokens} → {optimized_tokens} tokens")
        logger.info(f"  Compression: {compression_ratio:.1%}, Quality: {quality_preservation:.1%}")
        logger.info(f"  Processing time: {processing_time:.1f}ms")
        
        return result
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content caching"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _count_tokens(self, content: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple token estimation: ~1.3 tokens per word
        words = len(content.split())
        return int(words * 1.3)
    
    def _segment_content(self, content: str) -> List[ContextSegment]:
        """Segment content by type and importance"""
        segments = []
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for paragraph in paragraphs:
            # Identify content type
            content_type = self._identify_content_type(paragraph)
            
            # Calculate importance score
            importance_score = self._calculate_importance_score(paragraph, content_type)
            
            # Count tokens
            token_count = self._count_tokens(paragraph)
            
            # Check if essential
            is_essential = self._is_essential_content(paragraph)
            
            segment = ContextSegment(
                content=paragraph,
                content_type=content_type,
                importance_score=importance_score,
                token_count=token_count,
                is_essential=is_essential
            )
            
            segments.append(segment)
        
        return segments
    
    def _identify_content_type(self, content: str) -> ContentType:
        """Identify content type using patterns"""
        
        # Check each content type pattern
        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    return content_type
        
        # Check for specific keywords
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['claim', 'patent', 'invention']):
            return ContentType.LEGAL
        elif any(keyword in content_lower for keyword in ['technical', 'implementation', 'algorithm']):
            return ContentType.TECHNICAL
        elif any(keyword in content_lower for keyword in ['background', 'context', 'field']):
            return ContentType.BACKGROUND
        elif any(keyword in content_lower for keyword in ['example', 'embodiment', 'illustration']):
            return ContentType.EXAMPLES
        elif any(keyword in content_lower for keyword in ['reference', 'citation', 'bibliography']):
            return ContentType.REFERENCES
        else:
            return ContentType.METADATA
    
    def _calculate_importance_score(self, content: str, content_type: ContentType) -> float:
        """Calculate importance score for content"""
        
        base_score = 0.5
        
        # Content type base score
        type_scores = {
            ContentType.LEGAL: 0.9,
            ContentType.TECHNICAL: 0.8,
            ContentType.BACKGROUND: 0.6,
            ContentType.EXAMPLES: 0.7,
            ContentType.REFERENCES: 0.5,
            ContentType.METADATA: 0.3
        }
        
        base_score = type_scores.get(content_type, 0.5)
        
        # Keyword importance boost
        essential_keywords = self.config['essential_keywords']
        keyword_count = sum(1 for keyword in essential_keywords if keyword in content.lower())
        keyword_boost = min(keyword_count * 0.1, 0.3)
        
        # Length factor (longer content might be more important)
        length_factor = min(len(content) / 1000, 0.2)
        
        # Technical complexity factor
        technical_indicators = ['algorithm', 'method', 'system', 'apparatus', 'process']
        complexity_factor = sum(1 for indicator in technical_indicators if indicator in content.lower()) * 0.05
        
        final_score = min(base_score + keyword_boost + length_factor + complexity_factor, 1.0)
        
        return final_score
    
    def _is_essential_content(self, content: str) -> bool:
        """Check if content is essential and shouldn't be compressed"""
        
        essential_patterns = [
            r'(?i)claim\s+\d+',
            r'(?i)patent\s+application',
            r'(?i)invention\s+relates\s+to',
            r'(?i)method\s+comprises',
            r'(?i)system\s+includes',
            r'(?i)apparatus\s+comprises'
        ]
        
        return any(re.search(pattern, content) for pattern in essential_patterns)
    
    def _apply_optimization_strategies(self, segments: List[ContextSegment], 
                                     target_tokens: int, task_type: str = None,
                                     quality_requirement: float = 0.9) -> List[ContextSegment]:
        """Apply optimization strategies to segments"""
        
        optimized_segments = []
        
        for segment in segments:
            optimized_segment = self._optimize_segment(segment, task_type, quality_requirement)
            optimized_segments.append(optimized_segment)
        
        # Check if we need more aggressive optimization
        current_tokens = sum(seg.compressed_tokens for seg in optimized_segments)
        
        if current_tokens > target_tokens:
            # Apply more aggressive strategies
            optimized_segments = self._apply_aggressive_optimization(
                optimized_segments, target_tokens, quality_requirement
            )
        
        return optimized_segments
    
    def _optimize_segment(self, segment: ContextSegment, task_type: str = None,
                         quality_requirement: float = 0.9) -> ContextSegment:
        """Optimize a single segment"""
        
        if segment.is_essential:
            # Don't optimize essential content
            return segment
        
        # Determine compression ratio based on content type and importance
        base_compression = self.config['compression_ratios'].get(
            segment.content_type.value, 0.3
        )
        
        # Adjust compression based on importance
        importance_factor = 1.0 - segment.importance_score * 0.5
        compression_ratio = min(base_compression * importance_factor, 0.7)
        
        # Apply specific optimization strategies
        optimized_content = segment.content
        
        # Remove redundant information
        if OptimizationStrategy.REMOVE_REDUNDANT in self.config['strategies']:
            optimized_content = self._remove_redundant_content(optimized_content)
        
        # Summarize background information
        if (segment.content_type == ContentType.BACKGROUND and 
            OptimizationStrategy.SUMMARIZE_BACKGROUND in self.config['strategies']):
            optimized_content = self._summarize_background(optimized_content)
        
        # Truncate examples
        if (segment.content_type == ContentType.EXAMPLES and 
            OptimizationStrategy.TRUNCATE_EXAMPLES in self.config['strategies']):
            optimized_content = self._truncate_examples(optimized_content)
        
        # Compress references
        if (segment.content_type == ContentType.REFERENCES and 
            OptimizationStrategy.COMPRESS_REFERENCES in self.config['strategies']):
            optimized_content = self._compress_references(optimized_content)
        
        # Apply semantic compression
        if OptimizationStrategy.SEMANTIC_COMPRESSION in self.config['strategies']:
            optimized_content = self._apply_semantic_compression(optimized_content, compression_ratio)
        
        # Update segment
        optimized_segment = ContextSegment(
            content=optimized_content,
            content_type=segment.content_type,
            importance_score=segment.importance_score,
            token_count=self._count_tokens(optimized_content),
            is_essential=segment.is_essential,
            compression_ratio=1.0 - (self._count_tokens(optimized_content) / segment.token_count)
        )
        
        return optimized_segment
    
    def _remove_redundant_content(self, content: str) -> str:
        """Remove redundant and duplicate information"""
        
        # Remove duplicate sentences
        sentences = re.split(r'[.!?]+', content)
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen_sentences:
                unique_sentences.append(sentence)
                seen_sentences.add(sentence)
        
        # Remove redundant phrases
        redundant_phrases = [
            r'(?i)it\s+should\s+be\s+noted\s+that',
            r'(?i)it\s+is\s+important\s+to\s+note',
            r'(?i)as\s+mentioned\s+(?:above|previously)',
            r'(?i)in\s+other\s+words',
            r'(?i)that\s+is\s+to\s+say'
        ]
        
        optimized_content = '. '.join(unique_sentences)
        
        for phrase in redundant_phrases:
            optimized_content = re.sub(phrase, '', optimized_content)
        
        return optimized_content.strip()
    
    def _summarize_background(self, content: str) -> str:
        """Summarize background information"""
        
        # Simple summarization: keep first and last sentences of each paragraph
        paragraphs = content.split('\n')
        summarized_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            sentences = re.split(r'[.!?]+', paragraph)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 2:
                summarized_paragraphs.append(paragraph)
            else:
                # Keep first and last sentence
                summary = f"{sentences[0]}. {sentences[-1]}"
                summarized_paragraphs.append(summary)
        
        return '\n'.join(summarized_paragraphs)
    
    def _truncate_examples(self, content: str) -> str:
        """Truncate lengthy examples"""
        
        # Find example sections
        example_pattern = r'(?i)(example\s+\d+.*?)(?=example\s+\d+|\Z)'
        examples = re.findall(example_pattern, content, re.DOTALL)
        
        if not examples:
            return content
        
        # Truncate each example to key points
        truncated_examples = []
        for example in examples:
            # Keep first 3 sentences
            sentences = re.split(r'[.!?]+', example)
            key_sentences = sentences[:3]
            truncated = '. '.join(key_sentences) + '...'
            truncated_examples.append(truncated)
        
        return '\n\n'.join(truncated_examples)
    
    def _compress_references(self, content: str) -> str:
        """Compress reference information"""
        
        # Convert long references to abbreviated form
        lines = content.split('\n')
        compressed_lines = []
        
        for line in lines:
            if not line.strip():
                continue
            
            # Compress long reference lines
            if len(line) > 100:
                # Extract key information (author, title, year)
                parts = line.split(',')
                if len(parts) >= 3:
                    compressed = f"{parts[0]}, {parts[1]}, {parts[-1]}"
                    compressed_lines.append(compressed)
                else:
                    compressed_lines.append(line[:100] + '...')
            else:
                compressed_lines.append(line)
        
        return '\n'.join(compressed_lines)
    
    def _apply_semantic_compression(self, content: str, compression_ratio: float) -> str:
        """Apply semantic compression to content"""
        
        # Simple semantic compression: keep most important sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return content
        
        # Calculate how many sentences to keep
        target_sentences = max(1, int(len(sentences) * (1 - compression_ratio)))
        
        # Score sentences by importance
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence_importance(sentence)
            sentence_scores.append((score, i, sentence))
        
        # Sort by score and keep top sentences
        sentence_scores.sort(reverse=True)
        kept_sentences = sentence_scores[:target_sentences]
        
        # Sort by original order
        kept_sentences.sort(key=lambda x: x[1])
        
        # Reconstruct content
        compressed_content = '. '.join([s[2] for s in kept_sentences])
        
        return compressed_content
    
    def _score_sentence_importance(self, sentence: str) -> float:
        """Score sentence importance for compression"""
        
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Essential keywords
        essential_keywords = self.config['essential_keywords']
        keyword_count = sum(1 for keyword in essential_keywords if keyword in sentence_lower)
        score += keyword_count * 0.3
        
        # Technical terms
        technical_terms = ['method', 'system', 'apparatus', 'process', 'algorithm']
        tech_count = sum(1 for term in technical_terms if term in sentence_lower)
        score += tech_count * 0.2
        
        # Numbers and specifics
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # Length factor (not too short, not too long)
        words = len(sentence.split())
        if 10 <= words <= 30:
            score += 0.1
        
        return score
    
    def _apply_aggressive_optimization(self, segments: List[ContextSegment],
                                     target_tokens: int, quality_requirement: float) -> List[ContextSegment]:
        """Apply aggressive optimization when needed"""
        
        # Sort segments by importance (keep most important)
        segments.sort(key=lambda x: x.importance_score, reverse=True)
        
        optimized_segments = []
        current_tokens = 0
        
        for segment in segments:
            if current_tokens + segment.compressed_tokens <= target_tokens:
                optimized_segments.append(segment)
                current_tokens += segment.compressed_tokens
            elif segment.is_essential:
                # Always include essential content, even if over budget
                optimized_segments.append(segment)
                current_tokens += segment.compressed_tokens
            else:
                # Try to compress further
                if current_tokens < target_tokens:
                    remaining_tokens = target_tokens - current_tokens
                    if remaining_tokens > 0:
                        # Compress to fit
                        compression_ratio = 1.0 - (remaining_tokens / segment.token_count)
                        compressed_content = self._apply_semantic_compression(
                            segment.content, compression_ratio
                        )
                        
                        compressed_segment = ContextSegment(
                            content=compressed_content,
                            content_type=segment.content_type,
                            importance_score=segment.importance_score,
                            token_count=self._count_tokens(compressed_content),
                            is_essential=segment.is_essential,
                            compression_ratio=compression_ratio
                        )
                        
                        optimized_segments.append(compressed_segment)
                        current_tokens += compressed_segment.token_count
                        break
        
        return optimized_segments
    
    def _reconstruct_content(self, segments: List[ContextSegment]) -> str:
        """Reconstruct content from optimized segments"""
        
        # Sort segments by importance to maintain logical flow
        segments.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Group by content type for better organization
        grouped_segments = defaultdict(list)
        for segment in segments:
            grouped_segments[segment.content_type].append(segment)
        
        # Reconstruct in logical order
        content_order = [
            ContentType.LEGAL,
            ContentType.TECHNICAL,
            ContentType.BACKGROUND,
            ContentType.EXAMPLES,
            ContentType.REFERENCES,
            ContentType.METADATA
        ]
        
        reconstructed_parts = []
        for content_type in content_order:
            if content_type in grouped_segments:
                for segment in grouped_segments[content_type]:
                    reconstructed_parts.append(segment.content)
        
        return '\n\n'.join(reconstructed_parts)
    
    def _estimate_quality_preservation(self, original_segments: List[ContextSegment],
                                     optimized_segments: List[ContextSegment],
                                     task_type: str = None) -> float:
        """Estimate quality preservation after optimization"""
        
        # Calculate token preservation rate
        original_tokens = sum(seg.token_count for seg in original_segments)
        optimized_tokens = sum(seg.token_count for seg in optimized_segments)
        
        token_preservation = optimized_tokens / original_tokens if original_tokens > 0 else 0
        
        # Calculate importance preservation
        original_importance = sum(seg.importance_score * seg.token_count for seg in original_segments)
        optimized_importance = sum(seg.importance_score * seg.token_count for seg in optimized_segments)
        
        importance_preservation = optimized_importance / original_importance if original_importance > 0 else 0
        
        # Essential content preservation
        essential_original = sum(seg.token_count for seg in original_segments if seg.is_essential)
        essential_optimized = sum(seg.token_count for seg in optimized_segments if seg.is_essential)
        
        essential_preservation = essential_optimized / essential_original if essential_original > 0 else 1.0
        
        # Weighted average
        quality_score = (
            token_preservation * 0.3 +
            importance_preservation * 0.4 +
            essential_preservation * 0.3
        )
        
        return min(quality_score, 1.0)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        
        if not self.optimization_history:
            return {'message': 'No optimization history available'}
        
        total_optimizations = len(self.optimization_history)
        avg_compression = np.mean([opt.compression_ratio for opt in self.optimization_history])
        avg_quality = np.mean([opt.quality_preservation for opt in self.optimization_history])
        total_tokens_saved = sum(opt.token_savings for opt in self.optimization_history)
        total_cost_saved = sum(opt.cost_savings_estimate for opt in self.optimization_history)
        
        return {
            'total_optimizations': total_optimizations,
            'avg_compression_ratio': avg_compression,
            'avg_quality_preservation': avg_quality,
            'total_tokens_saved': total_tokens_saved,
            'total_cost_saved': total_cost_saved,
            'cache_hit_rate': len(self.cached_optimizations) / max(total_optimizations, 1)
        }
    
    def clear_cache(self):
        """Clear optimization cache"""
        self.cached_optimizations.clear()
        logger.info("Optimization cache cleared")

# Global optimizer instance
_context_optimizer = None

def get_context_optimizer() -> ContextOptimizer:
    """Get global context optimizer instance"""
    global _context_optimizer
    if _context_optimizer is None:
        _context_optimizer = ContextOptimizer()
    return _context_optimizer

def optimize_context(content: str, target_tokens: int = None, 
                    task_type: str = None, quality_requirement: float = 0.9) -> OptimizationResult:
    """Convenience function to optimize context"""
    optimizer = get_context_optimizer()
    return optimizer.optimize_context(content, target_tokens, task_type, quality_requirement) 