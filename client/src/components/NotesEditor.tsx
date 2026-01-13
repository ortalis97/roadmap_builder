import { useState, useEffect } from 'react';

interface NotesEditorProps {
  initialNotes: string;
  onSave: (notes: string) => void;
  isSaving?: boolean;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function NotesEditor({ initialNotes, onSave, isSaving = false }: NotesEditorProps) {
  const [notes, setNotes] = useState(initialNotes);
  const [hasChanges, setHasChanges] = useState(false);
  const debouncedNotes = useDebounce(notes, 500);

  useEffect(() => {
    setNotes(initialNotes);
    setHasChanges(false);
  }, [initialNotes]);

  useEffect(() => {
    if (hasChanges && debouncedNotes !== initialNotes) {
      onSave(debouncedNotes);
    }
  }, [debouncedNotes, hasChanges, initialNotes, onSave]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNotes(e.target.value);
    setHasChanges(true);
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-700">Notes</label>
        {isSaving && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <span className="animate-pulse">●</span> Saving...
          </span>
        )}
        {!isSaving && hasChanges && notes === debouncedNotes && (
          <span className="text-xs text-green-600">Saved</span>
        )}
      </div>
      <textarea
        value={notes}
        onChange={handleChange}
        placeholder="Add your notes here..."
        rows={6}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
      />
    </div>
  );
}
