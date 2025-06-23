import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useDrop } from 'react-dnd';
import { v4 as uuidv4 } from 'uuid';
import { Button } from '@/components/ui/button';
import { ZoomIn, ZoomOut, Maximize, Grid, Move, Link, Trash2 } from 'lucide-react';
import * as joint from '@joint/core';
import { ModelComponent } from '../../utils/calculationEngine';
import styles from './ModelCanvas.module.css';

interface ModelCanvasProps {
  model: { components: ModelComponent[] } | null;
  setModel: (model: { components: ModelComponent[] }) => void;
  selectedComponent: string | null;
  setSelectedComponent: (id: string | null) => void;
  calculations: Record<string, any>;
  getFormattedValue: (id: string) => string;
}

interface DropItem {
  type: string;
  componentType: string;
}

const ModelCanvas: React.FC<ModelCanvasProps> = ({
  model,
  setModel,
  selectedComponent,
  setSelectedComponent,
  calculations,
  getFormattedValue
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<joint.dia.Paper | null>(null);
  const graphRef = useRef<joint.dia.Graph | null>(null);
  const [zoom, setZoom] = useState(100);
  const [showGrid, setShowGrid] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionSource, setConnectionSource] = useState<string | null>(null);
  const [jointElements, setJointElements] = useState<Map<string, joint.dia.Element>>(new Map());

  // Initialize JointJS
  useEffect(() => {
    if (!canvasRef.current) return;

    // Create graph and paper
    const graph = new joint.dia.Graph();
    const paper = new joint.dia.Paper({
      el: canvasRef.current,
      model: graph,
      width: '100%',
      height: '100%',
      gridSize: 20,
      drawGrid: showGrid,
      background: {
        color: '#f8fafc'
      },
      interactive: {
        linkMove: false,
        elementMove: true,
        vertexMove: true,
        arrowheadMove: true
      },
      defaultLink: () => new joint.shapes.standard.Link({
        attrs: {
          line: {
            stroke: '#3b82f6',
            strokeWidth: 2,
            targetMarker: {
              type: 'path',
              d: 'M 10 -5 0 0 10 5 z',
              fill: '#3b82f6'
            }
          }
        }
      })
    });

    // Store references
    graphRef.current = graph;
    paperRef.current = paper;

    // Event handlers
    paper.on('element:pointerclick', (elementView: joint.dia.ElementView) => {
      const element = elementView.model;
      const componentId = element.get('componentId');
      if (componentId) {
        setSelectedComponent(componentId);
      }
    });

    paper.on('blank:pointerclick', () => {
      setSelectedComponent(null);
      setIsConnecting(false);
      setConnectionSource(null);
    });

    paper.on('element:pointerdblclick', (elementView: joint.dia.ElementView) => {
      const element = elementView.model;
      const componentId = element.get('componentId');
      if (componentId) {
        // Open properties panel or edit mode
        setSelectedComponent(componentId);
      }
    });

    // Cleanup
    return () => {
      paper.remove();
    };
  }, [setSelectedComponent]);

  // Update grid visibility
  useEffect(() => {
    if (paperRef.current) {
      paperRef.current.options.drawGrid = showGrid;
      paperRef.current.drawGrid();
    }
  }, [showGrid]);

  // Sync model components with JointJS elements
  useEffect(() => {
    if (!graphRef.current || !model) return;

    const graph = graphRef.current;
    
    // Clear existing elements
    graph.clear();
    setJointElements(new Map());

    // Create JointJS elements for each model component
    const newJointElements = new Map<string, joint.dia.Element>();

    model.components.forEach((component) => {
      const element = createJointElement(component);
      if (element) {
        graph.addCell(element);
        newJointElements.set(component.id, element);
      }
    });

    setJointElements(newJointElements);
  }, [model, calculations, getFormattedValue]);

  // Create JointJS element from model component
  const createJointElement = (component: ModelComponent): joint.dia.Element | null => {
    const position = component.position || { x: 100, y: 100 };
    const value = getFormattedValue(component.id);
    
    const baseAttrs = {
      body: {
        fill: getComponentColor(component.type),
        stroke: selectedComponent === component.id ? '#3b82f6' : '#e2e8f0',
        strokeWidth: selectedComponent === component.id ? 3 : 1,
        rx: 8,
        ry: 8
      },
      label: {
        text: `${component.type.replace('-', ' ').toUpperCase()}\n${value}`,
        fontSize: 12,
        fontFamily: 'Arial, sans-serif',
        fill: '#1f2937'
      }
    };

    const element = new joint.shapes.standard.Rectangle({
      position: { x: position.x, y: position.y },
      size: { width: 150, height: 80 },
      attrs: baseAttrs,
      componentId: component.id,
      componentType: component.type
    });

    return element;
  };

  // Get color for component type
  const getComponentColor = (type: string): string => {
    const colors: Record<string, string> = {
      'revenue-stream': '#10b981',
      'cost-center': '#ef4444',
      'roi-calculator': '#3b82f6',
      'npv-calculator': '#8b5cf6',
      'payback-calculator': '#f59e0b',
      'sensitivity-analysis': '#06b6d4',
      'variable': '#6b7280',
      'formula': '#ec4899',
      'investment': '#dc2626',
      'benefit': '#059669'
    };
    return colors[type] || '#6b7280';
  };

  // Handle drop from component library
  const [{ isOver }, drop] = useDrop({
    accept: 'component',
    drop: (item: DropItem, monitor) => {
      if (!canvasRef.current) return;

      const offset = monitor.getDropResult();
      const canvasRect = canvasRef.current.getBoundingClientRect();
      const clientOffset = monitor.getClientOffset();
      
      if (!clientOffset) return;

      const x = clientOffset.x - canvasRect.left;
      const y = clientOffset.y - canvasRect.top;

      addComponent(item.componentType, { x, y });
    },
    collect: (monitor) => ({
      isOver: monitor.isOver()
    })
  });

  // Add component to model
  const addComponent = useCallback((type: string, position: { x: number; y: number }) => {
    const newComponent: ModelComponent = {
      id: uuidv4(),
      type,
      properties: getDefaultProperties(type),
      position,
      connections: []
    };

    const updatedModel = {
      components: [...(model?.components || []), newComponent]
    };

    setModel(updatedModel);
    setSelectedComponent(newComponent.id);
  }, [model, setModel, setSelectedComponent]);

  // Get default properties for component type
  const getDefaultProperties = (type: string): Record<string, any> => {
    const defaults: Record<string, Record<string, any>> = {
      'revenue-stream': { unitPrice: 100, quantity: 10, growthRate: 5, periods: 12 },
      'cost-center': { monthlyCost: 1000, periods: 12, escalationRate: 3 },
      'roi-calculator': { investment: 10000, annualBenefit: 5000, periods: 3 },
      'npv-calculator': { cashFlows: [-10000, 3000, 4000, 5000], discountRate: 0.1 },
      'payback-calculator': { investment: 10000, annualCashFlow: 3000 },
      'sensitivity-analysis': { baseCase: 100, scenarios: [80, 90, 100, 110, 120] },
      'variable': { value: 0, name: 'Variable' },
      'formula': { formula: '0', name: 'Formula' }
    };
    return defaults[type] || { value: 0 };
  };

  // Delete selected component
  const deleteSelected = useCallback(() => {
    if (!selectedComponent || !model) return;

    const updatedModel = {
      components: model.components.filter(c => c.id !== selectedComponent)
    };

    setModel(updatedModel);
    setSelectedComponent(null);
  }, [selectedComponent, model, setModel, setSelectedComponent]);

  // Zoom functions
  const zoomIn = () => {
    const newZoom = Math.min(zoom + 25, 200);
    setZoom(newZoom);
    if (paperRef.current) {
      paperRef.current.scale(newZoom / 100);
    }
  };

  const zoomOut = () => {
    const newZoom = Math.max(zoom - 25, 50);
    setZoom(newZoom);
    if (paperRef.current) {
      paperRef.current.scale(newZoom / 100);
    }
  };

  const fitToWindow = () => {
    if (paperRef.current) {
      paperRef.current.scaleContentToFit();
      setZoom(100);
    }
  };

  // Combine canvas ref with drop ref
  const combinedRef = useCallback((node: HTMLDivElement) => {
    canvasRef.current = node;
    drop(node);
  }, [drop]);

  return (
    <div className="relative h-full bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-white rounded-lg shadow-lg p-2">
        <Button variant="outline" size="sm" onClick={zoomOut} disabled={zoom <= 50}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-sm font-medium min-w-[4rem] text-center">{zoom}%</span>
        <Button variant="outline" size="sm" onClick={zoomIn} disabled={zoom >= 200}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm" onClick={fitToWindow}>
          <Maximize className="h-4 w-4" />
        </Button>
        <div className="w-px h-6 bg-gray-300" />
        <Button 
          variant={showGrid ? "default" : "outline"} 
          size="sm" 
          onClick={() => setShowGrid(!showGrid)}
        >
          <Grid className="h-4 w-4" />
        </Button>
        <Button 
          variant={isConnecting ? "default" : "outline"} 
          size="sm"
          onClick={() => setIsConnecting(!isConnecting)}
        >
          <Link className="h-4 w-4" />
        </Button>
        {selectedComponent && (
          <Button variant="destructive" size="sm" onClick={deleteSelected}>
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Canvas */}
      <div 
        ref={combinedRef}
        className={`${styles.canvas} ${isOver ? styles.canvasDropOver : ''} ${isConnecting ? styles.canvasConnecting : styles.canvasDefault}`}
      />

      {/* Drop overlay */}
      {isOver && (
        <div className="absolute inset-0 bg-blue-100 bg-opacity-50 border-2 border-dashed border-blue-400 flex items-center justify-center z-5">
        <div className="bg-white px-4 py-2 rounded-lg shadow-lg">
          <p className="text-blue-600 font-medium">Drop component here</p>
        </div>
      </div>
      )}
    </div>
  );
};

export default ModelCanvas;
