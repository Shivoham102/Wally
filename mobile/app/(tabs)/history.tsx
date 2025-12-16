import { StyleSheet, View, Text, ScrollView } from 'react-native';
import { useColorScheme } from '@/components/useColorScheme';
import Colors from '@/constants/Colors';

export default function HistoryScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'dark'];

  // Placeholder data
  const orders = [
    { id: 1, date: 'Today, 2:30 PM', items: ['Milk', 'Eggs', 'Bread'], total: '$12.50' },
    { id: 2, date: 'Yesterday, 10:15 AM', items: ['Bananas', 'Apples', 'Orange Juice'], total: '$8.75' },
    { id: 3, date: 'Dec 14, 4:00 PM', items: ['Chicken Breast', 'Rice', 'Broccoli'], total: '$15.20' },
  ];

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.title, { color: colors.text }]}>Order History</Text>
      <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
        Your recent Walmart orders
      </Text>

      {orders.map((order) => (
        <View 
          key={order.id} 
          style={[styles.orderCard, { backgroundColor: colors.cardBackground, borderColor: colors.border }]}
        >
          <View style={styles.orderHeader}>
            <Text style={[styles.orderDate, { color: colors.textSecondary }]}>{order.date}</Text>
            <Text style={[styles.orderTotal, { color: colors.tint }]}>{order.total}</Text>
          </View>
          <View style={styles.itemsList}>
            {order.items.map((item, index) => (
              <View key={index} style={styles.itemRow}>
                <Text style={[styles.itemBullet, { color: colors.success }]}>•</Text>
                <Text style={[styles.itemText, { color: colors.text }]}>{item}</Text>
              </View>
            ))}
          </View>
          <View style={[styles.reorderButton, { borderColor: colors.border }]}>
            <Text style={[styles.reorderText, { color: colors.tint }]}>Reorder</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    marginBottom: 24,
  },
  orderCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  orderDate: {
    fontSize: 13,
    fontWeight: '500',
  },
  orderTotal: {
    fontSize: 16,
    fontWeight: '600',
  },
  itemsList: {
    marginBottom: 12,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  itemBullet: {
    fontSize: 16,
    marginRight: 8,
  },
  itemText: {
    fontSize: 15,
  },
  reorderButton: {
    borderTopWidth: 1,
    paddingTop: 12,
    alignItems: 'center',
  },
  reorderText: {
    fontSize: 15,
    fontWeight: '600',
  },
});

