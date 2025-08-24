# OpenAI Chat API Cost Estimation

## 📊 Current Configuration
- **Model**: `gpt-4o-mini` (recommended)
- **Max Tokens**: 300 per response
- **Temperature**: 0.7

## 💰 Pricing Breakdown (gpt-4o-mini)

### Per Token Costs:
- **Input tokens**: ~$0.15 per 1M tokens
- **Output tokens**: ~$0.60 per 1M tokens

### Typical Chat Request Analysis:
```
System Context (video metadata): ~600 tokens
User Question: ~20 tokens
AI Response: ~150 tokens (average)
-----------------------------------------
Total per chat: ~770 tokens = ~$0.0008
```

## 📈 Usage Cost Estimates

### Light Usage (100 chats/month):
- **Cost**: ~$0.08/month
- **Annual**: ~$0.96

### Moderate Usage (1,000 chats/month):
- **Cost**: ~$0.80/month  
- **Annual**: ~$9.60

### Heavy Usage (10,000 chats/month):
- **Cost**: ~$8.00/month
- **Annual**: ~$96.00

### Very Heavy Usage (50,000 chats/month):
- **Cost**: ~$40.00/month
- **Annual**: ~$480.00

## 🔧 Cost Optimization Options

### 1. Model Selection:
- **gpt-4o-mini**: Cheapest, good quality ✅ (Current)
- **gpt-3.5-turbo**: Even cheaper, lower quality
- **gpt-4o**: More expensive, highest quality

### 2. Response Length:
- Current: 300 max tokens
- Reduce to 200: ~33% cost reduction
- Reduce to 150: ~50% cost reduction

### 3. Context Optimization:
- Current: Full metadata summary
- Reduce metadata items: Fewer input tokens
- Smart filtering: Only relevant data

## 🎯 Recommended Settings

### Budget-Conscious:
```env
OPENAI_MODEL=gpt-3.5-turbo
CHAT_MAX_TOKENS=200
```
**Cost**: ~50% less than current

### Balanced (Current):
```env
OPENAI_MODEL=gpt-4o-mini
CHAT_MAX_TOKENS=300
```
**Cost**: ~$0.0008 per chat

### High-Quality:
```env
OPENAI_MODEL=gpt-4o
CHAT_MAX_TOKENS=400
```
**Cost**: ~3x current cost, best responses

## 📝 Notes
- Prices based on 2025 OpenAI pricing
- Actual costs may vary based on prompt complexity
- Monitor usage through OpenAI dashboard
- Set usage limits to prevent unexpected charges
