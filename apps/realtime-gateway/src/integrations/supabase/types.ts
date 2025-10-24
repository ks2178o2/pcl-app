export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.12 (cd3cf9e)"
  }
  public: {
    Tables: {
      appointments: {
        Row: {
          appointment_date: string
          created_at: string
          customer_name: string
          email: string | null
          id: string
          patient_id: string | null
          phone_number: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          appointment_date: string
          created_at?: string
          customer_name: string
          email?: string | null
          id?: string
          patient_id?: string | null
          phone_number?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          appointment_date?: string
          created_at?: string
          customer_name?: string
          email?: string | null
          id?: string
          patient_id?: string | null
          phone_number?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      call_analyses: {
        Row: {
          action_items_count: number | null
          analysis_data: Json
          analysis_version: string | null
          call_record_id: string
          created_at: string
          customer_engagement: number | null
          id: string
          model_used: string | null
          motivation_category: string | null
          objections_count: number | null
          overall_sentiment: string | null
          overall_urgency: number | null
          personality_type: string | null
          sales_performance_score: number | null
          status: string
          trust_level: number | null
          updated_at: string
          user_id: string
        }
        Insert: {
          action_items_count?: number | null
          analysis_data: Json
          analysis_version?: string | null
          call_record_id: string
          created_at?: string
          customer_engagement?: number | null
          id?: string
          model_used?: string | null
          motivation_category?: string | null
          objections_count?: number | null
          overall_sentiment?: string | null
          overall_urgency?: number | null
          personality_type?: string | null
          sales_performance_score?: number | null
          status?: string
          trust_level?: number | null
          updated_at?: string
          user_id: string
        }
        Update: {
          action_items_count?: number | null
          analysis_data?: Json
          analysis_version?: string | null
          call_record_id?: string
          created_at?: string
          customer_engagement?: number | null
          id?: string
          model_used?: string | null
          motivation_category?: string | null
          objections_count?: number | null
          overall_sentiment?: string | null
          overall_urgency?: number | null
          personality_type?: string | null
          sales_performance_score?: number | null
          status?: string
          trust_level?: number | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "call_analyses_call_record_id_fkey"
            columns: ["call_record_id"]
            isOneToOne: true
            referencedRelation: "call_records"
            referencedColumns: ["id"]
          },
        ]
      }
      call_chunks: {
        Row: {
          call_record_id: string
          chunk_number: number
          created_at: string
          duration_seconds: number
          file_path: string
          file_size: number
          id: string
          upload_status: string
          uploaded_at: string | null
        }
        Insert: {
          call_record_id: string
          chunk_number: number
          created_at?: string
          duration_seconds: number
          file_path: string
          file_size: number
          id?: string
          upload_status?: string
          uploaded_at?: string | null
        }
        Update: {
          call_record_id?: string
          chunk_number?: number
          created_at?: string
          duration_seconds?: number
          file_path?: string
          file_size?: number
          id?: string
          upload_status?: string
          uploaded_at?: string | null
        }
        Relationships: []
      }
      call_records: {
        Row: {
          audio_file_url: string | null
          center_id: string | null
          chunks_uploaded: number | null
          created_at: string
          customer_name: string
          diarization_confidence: number | null
          diarization_segments: Json | null
          duration_seconds: number | null
          end_time: string | null
          id: string
          is_active: boolean
          num_speakers: number | null
          organization_id: string | null
          recording_complete: boolean | null
          speaker_mapping: Json | null
          start_time: string
          total_chunks: number | null
          transcript: string | null
          transcription_confidence: number | null
          transcription_provider: string | null
          updated_at: string
          user_id: string
          vendor_insights: Json | null
        }
        Insert: {
          audio_file_url?: string | null
          center_id?: string | null
          chunks_uploaded?: number | null
          created_at?: string
          customer_name: string
          diarization_confidence?: number | null
          diarization_segments?: Json | null
          duration_seconds?: number | null
          end_time?: string | null
          id?: string
          is_active?: boolean
          num_speakers?: number | null
          organization_id?: string | null
          recording_complete?: boolean | null
          speaker_mapping?: Json | null
          start_time: string
          total_chunks?: number | null
          transcript?: string | null
          transcription_confidence?: number | null
          transcription_provider?: string | null
          updated_at?: string
          user_id: string
          vendor_insights?: Json | null
        }
        Update: {
          audio_file_url?: string | null
          center_id?: string | null
          chunks_uploaded?: number | null
          created_at?: string
          customer_name?: string
          diarization_confidence?: number | null
          diarization_segments?: Json | null
          duration_seconds?: number | null
          end_time?: string | null
          id?: string
          is_active?: boolean
          num_speakers?: number | null
          organization_id?: string | null
          recording_complete?: boolean | null
          speaker_mapping?: Json | null
          start_time?: string
          total_chunks?: number | null
          transcript?: string | null
          transcription_confidence?: number | null
          transcription_provider?: string | null
          updated_at?: string
          user_id?: string
          vendor_insights?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "call_records_center_id_fkey"
            columns: ["center_id"]
            isOneToOne: false
            referencedRelation: "centers"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "call_records_organization_id_fkey"
            columns: ["organization_id"]
            isOneToOne: false
            referencedRelation: "organizations"
            referencedColumns: ["id"]
          },
        ]
      }
      centers: {
        Row: {
          address: string | null
          created_at: string
          id: string
          name: string
          region_id: string
          updated_at: string
        }
        Insert: {
          address?: string | null
          created_at?: string
          id?: string
          name: string
          region_id: string
          updated_at?: string
        }
        Update: {
          address?: string | null
          created_at?: string
          id?: string
          name?: string
          region_id?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "centers_region_id_fkey"
            columns: ["region_id"]
            isOneToOne: false
            referencedRelation: "regions"
            referencedColumns: ["id"]
          },
        ]
      }
      compliance_settings: {
        Row: {
          auto_opt_out_keywords: string[] | null
          business_hours_end: string | null
          business_hours_only: boolean
          business_hours_start: string | null
          created_at: string
          id: string
          max_contact_attempts: number | null
          min_hours_between_contacts: number | null
          organization_id: string | null
          tcpa_compliance_enabled: boolean
          updated_at: string
          user_id: string
          weekend_contact_allowed: boolean
        }
        Insert: {
          auto_opt_out_keywords?: string[] | null
          business_hours_end?: string | null
          business_hours_only?: boolean
          business_hours_start?: string | null
          created_at?: string
          id?: string
          max_contact_attempts?: number | null
          min_hours_between_contacts?: number | null
          organization_id?: string | null
          tcpa_compliance_enabled?: boolean
          updated_at?: string
          user_id: string
          weekend_contact_allowed?: boolean
        }
        Update: {
          auto_opt_out_keywords?: string[] | null
          business_hours_end?: string | null
          business_hours_only?: boolean
          business_hours_start?: string | null
          created_at?: string
          id?: string
          max_contact_attempts?: number | null
          min_hours_between_contacts?: number | null
          organization_id?: string | null
          tcpa_compliance_enabled?: boolean
          updated_at?: string
          user_id?: string
          weekend_contact_allowed?: boolean
        }
        Relationships: []
      }
      contact_preferences: {
        Row: {
          call_record_id: string
          created_at: string
          customer_name: string
          do_not_contact: boolean
          email_allowed: boolean
          id: string
          notes: string | null
          phone_allowed: boolean
          preferred_contact_time: string | null
          sms_allowed: boolean
          timezone: string | null
          updated_at: string
          user_id: string
          voicemail_allowed: boolean
        }
        Insert: {
          call_record_id: string
          created_at?: string
          customer_name: string
          do_not_contact?: boolean
          email_allowed?: boolean
          id?: string
          notes?: string | null
          phone_allowed?: boolean
          preferred_contact_time?: string | null
          sms_allowed?: boolean
          timezone?: string | null
          updated_at?: string
          user_id: string
          voicemail_allowed?: boolean
        }
        Update: {
          call_record_id?: string
          created_at?: string
          customer_name?: string
          do_not_contact?: boolean
          email_allowed?: boolean
          id?: string
          notes?: string | null
          phone_allowed?: boolean
          preferred_contact_time?: string | null
          sms_allowed?: boolean
          timezone?: string | null
          updated_at?: string
          user_id?: string
          voicemail_allowed?: boolean
        }
        Relationships: []
      }
      email_activities: {
        Row: {
          call_record_id: string
          created_at: string
          delivery_status: string
          email_content: string
          email_type: string
          first_open_at: string | null
          id: string
          last_engagement_at: string | null
          opened_at: string | null
          recipient_email: string
          recipient_name: string
          sent_at: string
          subject: string
          total_opens: number
          total_read_time_seconds: number
          tracking_pixel_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          call_record_id: string
          created_at?: string
          delivery_status?: string
          email_content: string
          email_type?: string
          first_open_at?: string | null
          id?: string
          last_engagement_at?: string | null
          opened_at?: string | null
          recipient_email: string
          recipient_name: string
          sent_at?: string
          subject: string
          total_opens?: number
          total_read_time_seconds?: number
          tracking_pixel_id?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          call_record_id?: string
          created_at?: string
          delivery_status?: string
          email_content?: string
          email_type?: string
          first_open_at?: string | null
          id?: string
          last_engagement_at?: string | null
          opened_at?: string | null
          recipient_email?: string
          recipient_name?: string
          sent_at?: string
          subject?: string
          total_opens?: number
          total_read_time_seconds?: number
          tracking_pixel_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      email_templates: {
        Row: {
          content: string
          created_at: string
          id: string
          is_default: boolean
          name: string
          subject: string
          template_type: string
          updated_at: string
          user_id: string
        }
        Insert: {
          content: string
          created_at?: string
          id?: string
          is_default?: boolean
          name: string
          subject: string
          template_type?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          content?: string
          created_at?: string
          id?: string
          is_default?: boolean
          name?: string
          subject?: string
          template_type?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      follow_up_messages: {
        Row: {
          call_to_action: string
          channel_type: string
          created_at: string
          estimated_send_time: string | null
          follow_up_plan_id: string
          id: string
          message_content: string
          personalization_notes: string | null
          status: string
          subject_line: string | null
          tone: string
          updated_at: string
          user_id: string
        }
        Insert: {
          call_to_action: string
          channel_type: string
          created_at?: string
          estimated_send_time?: string | null
          follow_up_plan_id: string
          id?: string
          message_content: string
          personalization_notes?: string | null
          status?: string
          subject_line?: string | null
          tone?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          call_to_action?: string
          channel_type?: string
          created_at?: string
          estimated_send_time?: string | null
          follow_up_plan_id?: string
          id?: string
          message_content?: string
          personalization_notes?: string | null
          status?: string
          subject_line?: string | null
          tone?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "follow_up_messages_follow_up_plan_id_fkey"
            columns: ["follow_up_plan_id"]
            isOneToOne: false
            referencedRelation: "follow_up_plans"
            referencedColumns: ["id"]
          },
        ]
      }
      follow_up_plans: {
        Row: {
          call_record_id: string
          compliance_notes: string | null
          created_at: string
          customer_urgency: string
          id: string
          next_action: string
          priority_score: number
          reasoning: string
          recommended_timing: string
          status: string
          strategy_type: string
          updated_at: string
          user_id: string
        }
        Insert: {
          call_record_id: string
          compliance_notes?: string | null
          created_at?: string
          customer_urgency: string
          id?: string
          next_action: string
          priority_score?: number
          reasoning: string
          recommended_timing: string
          status?: string
          strategy_type: string
          updated_at?: string
          user_id: string
        }
        Update: {
          call_record_id?: string
          compliance_notes?: string | null
          created_at?: string
          customer_urgency?: string
          id?: string
          next_action?: string
          priority_score?: number
          reasoning?: string
          recommended_timing?: string
          status?: string
          strategy_type?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      networks: {
        Row: {
          created_at: string
          id: string
          name: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          name: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string
          updated_at?: string
        }
        Relationships: []
      }
      organizations: {
        Row: {
          business_type: string | null
          created_at: string
          id: string
          name: string
          updated_at: string
        }
        Insert: {
          business_type?: string | null
          created_at?: string
          id?: string
          name: string
          updated_at?: string
        }
        Update: {
          business_type?: string | null
          created_at?: string
          id?: string
          name?: string
          updated_at?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          created_at: string
          id: string
          organization_id: string | null
          salesperson_name: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          organization_id?: string | null
          salesperson_name: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          organization_id?: string | null
          salesperson_name?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "profiles_organization_id_fkey"
            columns: ["organization_id"]
            isOneToOne: false
            referencedRelation: "organizations"
            referencedColumns: ["id"]
          },
        ]
      }
      regions: {
        Row: {
          created_at: string
          id: string
          name: string
          network_id: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          name: string
          network_id: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string
          network_id?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "regions_network_id_fkey"
            columns: ["network_id"]
            isOneToOne: false
            referencedRelation: "networks"
            referencedColumns: ["id"]
          },
        ]
      }
      sms_activities: {
        Row: {
          call_record_id: string | null
          created_at: string
          delivered_at: string | null
          delivery_status: string | null
          id: string
          message_content: string
          message_type: string | null
          recipient_name: string | null
          recipient_phone: string
          sent_at: string | null
          twilio_message_sid: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          call_record_id?: string | null
          created_at?: string
          delivered_at?: string | null
          delivery_status?: string | null
          id?: string
          message_content: string
          message_type?: string | null
          recipient_name?: string | null
          recipient_phone: string
          sent_at?: string | null
          twilio_message_sid?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          call_record_id?: string | null
          created_at?: string
          delivered_at?: string | null
          delivery_status?: string | null
          id?: string
          message_content?: string
          message_type?: string | null
          recipient_name?: string | null
          recipient_phone?: string
          sent_at?: string | null
          twilio_message_sid?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      user_assignments: {
        Row: {
          center_id: string | null
          created_at: string
          id: string
          network_id: string | null
          region_id: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          center_id?: string | null
          created_at?: string
          id?: string
          network_id?: string | null
          region_id?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          center_id?: string | null
          created_at?: string
          id?: string
          network_id?: string | null
          region_id?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_assignments_center_id_fkey"
            columns: ["center_id"]
            isOneToOne: false
            referencedRelation: "centers"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "user_assignments_network_id_fkey"
            columns: ["network_id"]
            isOneToOne: false
            referencedRelation: "networks"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "user_assignments_region_id_fkey"
            columns: ["region_id"]
            isOneToOne: false
            referencedRelation: "regions"
            referencedColumns: ["id"]
          },
        ]
      }
      user_roles: {
        Row: {
          created_at: string
          id: string
          role: Database["public"]["Enums"]["user_role"]
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          role: Database["public"]["Enums"]["user_role"]
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          role?: Database["public"]["Enums"]["user_role"]
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      voice_profiles: {
        Row: {
          audio_sample_url: string | null
          confidence_score: number | null
          created_at: string
          id: string
          profile_type: string
          sample_duration_seconds: number | null
          sample_text: string | null
          speaker_name: string
          updated_at: string
          user_id: string
          voice_embedding: Json | null
        }
        Insert: {
          audio_sample_url?: string | null
          confidence_score?: number | null
          created_at?: string
          id?: string
          profile_type: string
          sample_duration_seconds?: number | null
          sample_text?: string | null
          speaker_name: string
          updated_at?: string
          user_id: string
          voice_embedding?: Json | null
        }
        Update: {
          audio_sample_url?: string | null
          confidence_score?: number | null
          created_at?: string
          id?: string
          profile_type?: string
          sample_duration_seconds?: number | null
          sample_text?: string | null
          speaker_name?: string
          updated_at?: string
          user_id?: string
          voice_embedding?: Json | null
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      decrypt_sensitive_data: {
        Args: { encrypted_data: string }
        Returns: string
      }
      encrypt_sensitive_data: {
        Args: { data: string }
        Returns: string
      }
      get_user_accessible_centers: {
        Args: { _user_id: string }
        Returns: {
          center_id: string
        }[]
      }
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["user_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      user_role: "doctor" | "salesperson" | "coach" | "leader" | "system_admin"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      user_role: ["doctor", "salesperson", "coach", "leader", "system_admin"],
    },
  },
} as const
