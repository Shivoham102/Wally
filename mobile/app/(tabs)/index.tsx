import { StyleSheet, View, Text, Pressable, ActivityIndicator, ScrollView } from 'react-native';
import { useState, useEffect } from 'react';
import { Audio } from 'expo-av';
import { useColorScheme } from '@/components/useColorScheme';
import Colors from '@/constants/Colors';
import { processVoiceCommand, testConnection } from '@/api/voice';
import { addItemsToCartStructured } from '@/api/automation';

type RecordingStatus = 'idle' | 'recording' | 'processing' | 'confirming';

interface ItemWithQuantity {
  item: string;
  quantity: number;
}

interface CommandResult {
  transcription: string;
  intent: {
    type: string;
    items?: ItemWithQuantity[];
  };
  status: string;
}

export default function VoiceScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'dark'];
  
  const [status, setStatus] = useState<RecordingStatus>('idle');
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [error, setError] = useState<string>('');
  const [connected, setConnected] = useState<boolean | null>(null);
  const [automationStatus, setAutomationStatus] = useState<string>('');

  // Request permissions and test connection on mount
  useEffect(() => {
    (async () => {
      const isConnected = await testConnection();
      setConnected(isConnected);
      console.log('Backend connected:', isConnected);
      
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        setError('Microphone permission is required');
      }
    })();
  }, []);

  const startRecording = async () => {
    try {
      setError('');
      setResult(null);
      setAutomationStatus('');
      
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      
      setRecording(recording);
      setStatus('recording');
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to start recording');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      setStatus('processing');
      
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      if (!uri) {
        throw new Error('No recording URI');
      }

      // Process command - get transcription + intent
      const commandResult = await processVoiceCommand(uri);
      console.log('Command result:', commandResult);
      setResult(commandResult);
      setStatus('confirming');
    } catch (err: any) {
      console.error('Failed to process recording:', err);
      setError(err.message || 'Failed to process recording');
      setStatus('idle');
    }
  };

  const handleMicPress = () => {
    if (status === 'idle' || status === 'confirming') {
      startRecording();
    } else if (status === 'recording') {
      stopRecording();
    }
  };

  const handleAddToCart = async () => {
    if (!result?.intent?.items?.length) return;
    
    try {
      setAutomationStatus('Adding items to cart...');
      // Pass the items with quantity to automation
      const automationResult = await addItemsToCartStructured(result.intent.items);
      console.log('Automation result:', automationResult);
      setAutomationStatus('✓ Items added to cart!');
    } catch (err: any) {
      console.error('Automation failed:', err);
      setAutomationStatus(`❌ Failed: ${err.message}`);
    }
  };

  const handleCancel = () => {
    setResult(null);
    setStatus('idle');
    setAutomationStatus('');
  };

  const getStatusText = () => {
    if (connected === false) return 'Not Connected';
    if (connected === null) return 'Connecting...';
    switch (status) {
      case 'recording':
        return 'Recording...';
      case 'processing':
        return 'Processing...';
      case 'confirming':
        return 'Review Items';
      default:
        return 'Ready';
    }
  };

  const getStatusColor = () => {
    if (connected === false) return colors.error;
    if (connected === null) return colors.textSecondary;
    switch (status) {
      case 'recording':
        return colors.error;
      case 'processing':
        return colors.tint;
      case 'confirming':
        return colors.success;
      default:
        return colors.success;
    }
  };

  const getButtonStyle = () => {
    if (status === 'recording') {
      return [styles.micButton, styles.micButtonRecording, { backgroundColor: colors.error }];
    }
    if (status === 'confirming') {
      return [styles.micButton, styles.micButtonSmall, { backgroundColor: colors.cardBackground, borderColor: colors.border, borderWidth: 2 }];
    }
    return [styles.micButton, { backgroundColor: colors.tint }];
  };

  const getInstructions = () => {
    switch (status) {
      case 'recording':
        return 'Tap to stop recording';
      case 'processing':
        return 'Understanding your command...';
      case 'confirming':
        return 'Tap mic to try again';
      default:
        return 'Tap to start recording';
    }
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]} contentContainerStyle={styles.contentContainer}>
      {/* Status indicator */}
      <View style={[styles.statusBadge, { backgroundColor: colors.cardBackground, borderColor: colors.border }]}>
        <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
        <Text style={[styles.statusText, { color: colors.textSecondary }]}>{getStatusText()}</Text>
      </View>

      {/* Main microphone button */}
      <View style={styles.micContainer}>
        <Pressable 
          style={getButtonStyle()}
          onPress={handleMicPress}
          disabled={status === 'processing'}
        >
          {status === 'processing' ? (
            <ActivityIndicator size="large" color="#FFFFFF" />
          ) : (
            <Text style={[styles.micIcon, status === 'confirming' && styles.micIconSmall]}>
              {status === 'recording' ? '⏹️' : '🎤'}
            </Text>
          )}
        </Pressable>
        <Text style={[styles.instructions, { color: colors.textSecondary }]}>
          {getInstructions()}
        </Text>
      </View>

      {/* Error display */}
      {error ? (
        <View style={[styles.errorBox, { backgroundColor: colors.cardBackground, borderColor: colors.error }]}>
          <Text style={[styles.errorText, { color: colors.error }]}>{error}</Text>
        </View>
      ) : null}

      {/* Transcription display */}
      {result?.transcription ? (
        <View style={[styles.resultBox, { backgroundColor: colors.cardBackground, borderColor: colors.border }]}>
          <Text style={[styles.resultLabel, { color: colors.textSecondary }]}>You said:</Text>
          <Text style={[styles.transcriptionText, { color: colors.text }]}>"{result.transcription}"</Text>
        </View>
      ) : null}

      {/* Items list */}
      {result?.intent?.items?.length ? (
        <View style={[styles.itemsBox, { backgroundColor: colors.cardBackground, borderColor: colors.border }]}>
          <Text style={[styles.resultLabel, { color: colors.textSecondary }]}>
            Items detected ({result.intent.items.length}):
          </Text>
          {result.intent.items.map((item, index) => (
            <View key={index} style={styles.itemRow}>
              <Text style={[styles.itemBullet, { color: colors.success }]}>•</Text>
              <Text style={[styles.itemText, { color: colors.text }]}>
                {item.quantity > 1 ? `${item.quantity}x ` : ''}{item.item}
              </Text>
            </View>
          ))}
          
          {/* Action buttons */}
          {!automationStatus ? (
            <View style={styles.actionButtons}>
              <Pressable 
                style={[styles.actionButton, styles.cancelButton, { borderColor: colors.border }]}
                onPress={handleCancel}
              >
                <Text style={[styles.cancelButtonText, { color: colors.textSecondary }]}>Cancel</Text>
              </Pressable>
              <Pressable 
                style={[styles.actionButton, styles.addButton, { backgroundColor: colors.success }]}
                onPress={handleAddToCart}
              >
                <Text style={styles.addButtonText}>Add to Cart</Text>
              </Pressable>
            </View>
          ) : (
            <View style={styles.automationStatus}>
              <Text style={[styles.automationText, { color: colors.success }]}>{automationStatus}</Text>
            </View>
          )}
        </View>
      ) : null}

      {/* Placeholder when no result */}
      {!result && status === 'idle' && (
        <View style={[styles.placeholderBox, { backgroundColor: colors.cardBackground, borderColor: colors.border }]}>
          <Text style={[styles.placeholderText, { color: colors.textSecondary }]}>
            Say something like:{'\n'}
            "Add milk, eggs, and bread"{'\n'}
            "Order my usual groceries"
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    alignItems: 'center',
    paddingTop: 30,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    marginBottom: 40,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  micContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  micButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#1F6FEB',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  micButtonRecording: {
    shadowColor: '#F85149',
  },
  micButtonSmall: {
    width: 60,
    height: 60,
    borderRadius: 30,
    shadowOpacity: 0,
    elevation: 0,
  },
  micIcon: {
    fontSize: 40,
  },
  micIconSmall: {
    fontSize: 24,
  },
  instructions: {
    fontSize: 14,
  },
  errorBox: {
    width: '100%',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  resultBox: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 16,
  },
  resultLabel: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  transcriptionText: {
    fontSize: 16,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  itemsBox: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  itemBullet: {
    fontSize: 18,
    marginRight: 10,
  },
  itemText: {
    fontSize: 16,
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  cancelButton: {
    borderWidth: 1,
  },
  cancelButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  addButton: {},
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  automationStatus: {
    marginTop: 16,
    alignItems: 'center',
  },
  automationText: {
    fontSize: 15,
    fontWeight: '600',
  },
  placeholderBox: {
    width: '100%',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  placeholderText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
});
