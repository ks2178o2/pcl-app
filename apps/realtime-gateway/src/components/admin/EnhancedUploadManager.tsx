// apps/realtime-gateway/src/components/admin/EnhancedUploadManager.tsx

import React, { useState, useRef } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Progress 
} from '@/components/ui/progress';
import { 
  Upload, 
  FileText, 
  Link, 
  Database, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Download,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { RAGFeatureSelector } from '@/components/rag/RAGFeatureSelector';
import { useAuth } from '@/hooks/useAuth';

interface UploadResult {
  id: string;
  type: 'file' | 'web_scrape' | 'bulk_api';
  filename?: string;
  url?: string;
  items_count: number;
  success_count: number;
  error_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  processed_items?: string[];
  errors?: string[];
}

interface BulkItem {
  item_id: string;
  item_type: string;
  item_title: string;
  item_content: string;
  priority?: number;
  confidence_score?: number;
  tags?: string[];
}

export const EnhancedUploadManager: React.FC = () => {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State management
  const [activeTab, setActiveTab] = useState('file');
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileRagFeature, setFileRagFeature] = useState('');
  const [fileMetadata, setFileMetadata] = useState('');

  // Web scraping state
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeRagFeature, setScrapeRagFeature] = useState('');

  // Bulk API state
  const [bulkItems, setBulkItems] = useState<BulkItem[]>([]);
  const [bulkRagFeature, setBulkRagFeature] = useState('');
  const [bulkJsonInput, setBulkJsonInput] = useState('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile || !fileRagFeature) {
      alert('Please select a file and specify the RAG feature');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('rag_feature', fileRagFeature);
      formData.append('metadata', fileMetadata);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/enhanced-context/upload/file', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await response.json();
      
      if (data.success) {
        const result: UploadResult = {
          id: `upload-${Date.now()}`,
          type: 'file',
          filename: selectedFile.name,
          items_count: data.success_count + data.error_count,
          success_count: data.success_count,
          error_count: data.error_count,
          status: 'completed',
          created_at: new Date().toISOString(),
          processed_items: data.processed_items,
        };
        
        setUploadResults(prev => [result, ...prev]);
        setSelectedFile(null);
        setFileRagFeature('');
        setFileMetadata('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('File upload error:', error);
      const result: UploadResult = {
        id: `upload-${Date.now()}`,
        type: 'file',
        filename: selectedFile.name,
        items_count: 0,
        success_count: 0,
        error_count: 1,
        status: 'failed',
        created_at: new Date().toISOString(),
        errors: [error instanceof Error ? error.message : 'Upload failed'],
      };
      setUploadResults(prev => [result, ...prev]);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleWebScrape = async () => {
    if (!scrapeUrl || !scrapeRagFeature) {
      alert('Please provide a URL and specify the RAG feature');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 15, 90));
      }, 300);

      const response = await fetch('/api/enhanced-context/upload/web-scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: scrapeUrl,
          rag_feature: scrapeRagFeature,
        }),
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await response.json();
      
      if (data.success) {
        const result: UploadResult = {
          id: `scrape-${Date.now()}`,
          type: 'web_scrape',
          url: scrapeUrl,
          items_count: 1,
          success_count: 1,
          error_count: 0,
          status: 'completed',
          created_at: new Date().toISOString(),
          processed_items: [data.scraped_item],
        };
        
        setUploadResults(prev => [result, ...prev]);
        setScrapeUrl('');
        setScrapeRagFeature('');
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Web scrape error:', error);
      const result: UploadResult = {
        id: `scrape-${Date.now()}`,
        type: 'web_scrape',
        url: scrapeUrl,
        items_count: 0,
        success_count: 0,
        error_count: 1,
        status: 'failed',
        created_at: new Date().toISOString(),
        errors: [error instanceof Error ? error.message : 'Scraping failed'],
      };
      setUploadResults(prev => [result, ...prev]);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleBulkUpload = async () => {
    if (!bulkRagFeature || bulkItems.length === 0) {
      alert('Please specify the RAG feature and add items');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 5, 90));
      }, 100);

      const response = await fetch('/api/enhanced-context/upload/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: bulkItems,
          rag_feature: bulkRagFeature,
        }),
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await response.json();
      
      if (data.success) {
        const result: UploadResult = {
          id: `bulk-${Date.now()}`,
          type: 'bulk_api',
          items_count: bulkItems.length,
          success_count: data.success_count,
          error_count: data.error_count,
          status: 'completed',
          created_at: new Date().toISOString(),
          processed_items: data.processed_items,
        };
        
        setUploadResults(prev => [result, ...prev]);
        setBulkItems([]);
        setBulkRagFeature('');
        setBulkJsonInput('');
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Bulk upload error:', error);
      const result: UploadResult = {
        id: `bulk-${Date.now()}`,
        type: 'bulk_api',
        items_count: bulkItems.length,
        success_count: 0,
        error_count: bulkItems.length,
        status: 'failed',
        created_at: new Date().toISOString(),
        errors: [error instanceof Error ? error.message : 'Bulk upload failed'],
      };
      setUploadResults(prev => [result, ...prev]);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const addBulkItem = () => {
    const newItem: BulkItem = {
      item_id: `bulk-item-${Date.now()}`,
      item_type: 'knowledge_chunk',
      item_title: '',
      item_content: '',
      priority: 1,
      confidence_score: 0.8,
      tags: [],
    };
    setBulkItems(prev => [...prev, newItem]);
  };

  const updateBulkItem = (index: number, field: keyof BulkItem, value: any) => {
    setBulkItems(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const removeBulkItem = (index: number) => {
    setBulkItems(prev => prev.filter((_, i) => i !== index));
  };

  const parseBulkJson = () => {
    try {
      const parsed = JSON.parse(bulkJsonInput);
      if (Array.isArray(parsed)) {
        setBulkItems(parsed);
        setBulkJsonInput('');
      } else {
        alert('JSON must be an array of items');
      }
    } catch (error) {
      alert('Invalid JSON format');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'file':
        return <FileText className="h-4 w-4" />;
      case 'web_scrape':
        return <Link className="h-4 w-4" />;
      case 'bulk_api':
        return <Database className="h-4 w-4" />;
      default:
        return <Upload className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Enhanced Upload Manager</h2>
          <p className="text-gray-600">
            Upload knowledge content via files, web scraping, or bulk API
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          <span className="text-sm text-gray-500">
            {uploadResults.length} uploads
          </span>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="file" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            File Upload
          </TabsTrigger>
          <TabsTrigger value="web" className="flex items-center gap-2">
            <Link className="h-4 w-4" />
            Web Scraping
          </TabsTrigger>
          <TabsTrigger value="bulk" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Bulk API
          </TabsTrigger>
        </TabsList>

        {/* File Upload Tab */}
        <TabsContent value="file" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                File Upload
              </CardTitle>
              <CardDescription>
                Upload documents (PDF, DOCX, TXT, MD) and extract knowledge
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="file-input">Select File</Label>
                <Input
                  ref={fileInputRef}
                  id="file-input"
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={handleFileSelect}
                  className="mt-1"
                />
                {selectedFile && (
                  <p className="text-sm text-gray-600 mt-1">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              <div>
                <RAGFeatureSelector
                  value={fileRagFeature}
                  onChange={setFileRagFeature}
                  organizationId={user?.organization_id || ''}
                  filterByCategory="sales"
                  placeholder="Select RAG feature for file upload..."
                />
              </div>

              <div>
                <Label htmlFor="file-metadata">Metadata (JSON)</Label>
                <Textarea
                  id="file-metadata"
                  value={fileMetadata}
                  onChange={(e) => setFileMetadata(e.target.value)}
                  placeholder='{"source": "company_docs", "category": "sales"}'
                  rows={3}
                  className="mt-1"
                />
              </div>

              <Button 
                onClick={handleFileUpload} 
                disabled={!selectedFile || !fileRagFeature || uploading}
                className="w-full"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload File
                  </>
                )}
              </Button>

              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} className="w-full" />
                  <p className="text-sm text-center text-gray-600">
                    Processing file... {uploadProgress}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Web Scraping Tab */}
        <TabsContent value="web" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link className="h-5 w-5" />
                Web Scraping
              </CardTitle>
              <CardDescription>
                Scrape content from web pages and add to knowledge base
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="scrape-url">URL</Label>
                <Input
                  id="scrape-url"
                  value={scrapeUrl}
                  onChange={(e) => setScrapeUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="mt-1"
                />
              </div>

              <div>
                <RAGFeatureSelector
                  value={scrapeRagFeature}
                  onChange={setScrapeRagFeature}
                  organizationId={user?.organization_id || ''}
                  filterByCategory="sales"
                  placeholder="Select RAG feature for web scraping..."
                />
              </div>

              <Button 
                onClick={handleWebScrape} 
                disabled={!scrapeUrl || !scrapeRagFeature || uploading}
                className="w-full"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  <>
                    <Link className="h-4 w-4 mr-2" />
                    Scrape Content
                  </>
                )}
              </Button>

              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} className="w-full" />
                  <p className="text-sm text-center text-gray-600">
                    Scraping content... {uploadProgress}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bulk API Tab */}
        <TabsContent value="bulk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Bulk API Upload
              </CardTitle>
              <CardDescription>
                Upload multiple knowledge items via API
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <RAGFeatureSelector
                  value={bulkRagFeature}
                  onChange={setBulkRagFeature}
                  organizationId={user?.organization_id || ''}
                  filterByCategory="sales"
                  placeholder="Select RAG feature for bulk upload..."
                />
              </div>

              <div>
                <Label htmlFor="bulk-json">Bulk JSON Input</Label>
                <Textarea
                  id="bulk-json"
                  value={bulkJsonInput}
                  onChange={(e) => setBulkJsonInput(e.target.value)}
                  placeholder='[{"item_id": "item1", "item_type": "knowledge_chunk", "item_title": "Title", "item_content": "Content"}]'
                  rows={4}
                  className="mt-1"
                />
                <Button 
                  onClick={parseBulkJson} 
                  disabled={!bulkJsonInput}
                  className="mt-2"
                  variant="outline"
                >
                  Parse JSON
                </Button>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Items ({bulkItems.length})</Label>
                  <Button onClick={addBulkItem} size="sm">
                    <Upload className="h-4 w-4 mr-1" />
                    Add Item
                  </Button>
                </div>

                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {bulkItems.map((item, index) => (
                    <Card key={index} className="p-3">
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            placeholder="Item ID"
                            value={item.item_id}
                            onChange={(e) => updateBulkItem(index, 'item_id', e.target.value)}
                          />
                          <Input
                            placeholder="Item Type"
                            value={item.item_type}
                            onChange={(e) => updateBulkItem(index, 'item_type', e.target.value)}
                          />
                        </div>
                        <Input
                          placeholder="Title"
                          value={item.item_title}
                          onChange={(e) => updateBulkItem(index, 'item_title', e.target.value)}
                        />
                        <Textarea
                          placeholder="Content"
                          value={item.item_content}
                          onChange={(e) => updateBulkItem(index, 'item_content', e.target.value)}
                          rows={2}
                        />
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              placeholder="Priority"
                              value={item.priority || 1}
                              onChange={(e) => updateBulkItem(index, 'priority', parseInt(e.target.value))}
                              className="w-20"
                            />
                            <Input
                              type="number"
                              step="0.1"
                              min="0"
                              max="1"
                              placeholder="Confidence"
                              value={item.confidence_score || 0.8}
                              onChange={(e) => updateBulkItem(index, 'confidence_score', parseFloat(e.target.value))}
                              className="w-24"
                            />
                          </div>
                          <Button 
                            onClick={() => removeBulkItem(index)} 
                            size="sm" 
                            variant="outline"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              <Button 
                onClick={handleBulkUpload} 
                disabled={bulkItems.length === 0 || !bulkRagFeature || uploading}
                className="w-full"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    Upload {bulkItems.length} Items
                  </>
                )}
              </Button>

              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} className="w-full" />
                  <p className="text-sm text-center text-gray-600">
                    Processing bulk upload... {uploadProgress}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Upload Results
            </CardTitle>
            <CardDescription>
              Recent upload activity and results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {uploadResults.map((result) => (
                <div key={result.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getTypeIcon(result.type)}
                    <div>
                      <p className="font-medium">
                        {result.type === 'file' && result.filename}
                        {result.type === 'web_scrape' && result.url}
                        {result.type === 'bulk_api' && `Bulk Upload (${result.items_count} items)`}
                      </p>
                      <p className="text-sm text-gray-600">
                        {result.success_count} successful, {result.error_count} failed
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(result.status)}
                    <span className="text-sm text-gray-600">
                      {new Date(result.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
